/**
 * Cloudflare Pages Function
 * 处理 /api/interpret 的 POST 请求
 * 功能：作为网关，处理“解梦”和“象征查询”两种请求
 * 更新日志：
 * 1. 升级模型至 gemini-2.5-flash 以提升基准速度
 * 2. 显式关闭 thinkingConfig (includeThoughts: false) 以减少推理延迟
 * 3. 保留 CORS 和 指数退避重试机制
 */

// 定义通用的 CORS 头部
const corsHeaders = {
  'Access-Control-Allow-Origin': '*', // 允许所有来源
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

// 辅助函数：休眠
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// 辅助函数：带指数退避的 Fetch 重试逻辑
async function fetchWithRetry(url, options, maxRetries = 3) {
  let delay = 1000; // 初始等待 1 秒

  for (let i = 0; i <= maxRetries; i++) {
    try {
      const response = await fetch(url, options);

      // 如果请求成功 (2xx)，直接返回
      if (response.ok) {
        return response;
      }

      // 处理特定的错误状态码
      // 429: Too Many Requests (频率限制) -> 需要重试
      // 503: Service Unavailable (服务暂时不可用) -> 需要重试
      if (response.status === 429 || response.status === 503) {
        if (i === maxRetries) {
          console.warn(`Max retries reached for ${response.status}. Giving up.`);
          return response; // 最后一次尝试如果还是失败，返回错误响应给前端处理
        }

        console.warn(`Hit ${response.status}. Retrying in ${delay}ms... (Attempt ${i + 1}/${maxRetries})`);
        await sleep(delay);
        delay *= 2; // 指数退避：1s -> 2s -> 4s
        continue;
      }

      // 其他错误 (如 400 Bad Request, 401 Unauthorized, 403 Forbidden, 500 Internal Server Error)
      return response;

    } catch (error) {
      // 处理网络层面的错误 (如 DNS 失败, 连接超时)
      if (i === maxRetries) throw error;
      
      console.warn(`Network error: ${error.message}. Retrying in ${delay}ms...`);
      await sleep(delay);
      delay *= 2;
    }
  }
}

// 处理 OPTIONS 预检请求
export async function onRequestOptions(context) {
  return new Response(null, {
    status: 204,
    headers: corsHeaders
  });
}

export async function onRequestPost(context) {
  try {
    const { request, env } = context;
    
    // 验证请求方法
    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ error: "Method not allowed" }), {
        status: 405,
        headers: { 
            'Content-Type': 'application/json', 
            'Allow': 'POST',
            ...corsHeaders 
        }
      });
    }

    const contentType = request.headers.get('Content-Type');
    if (!contentType || !contentType.includes('application/json')) {
      return new Response(JSON.stringify({ error: "Unsupported Media Type. Use application/json" }), {
        status: 415,
        headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders
        }
      });
    }

    // 解析请求体
    let body;
    try {
      body = await request.json();
    } catch (parseError) {
      return new Response(JSON.stringify({ error: "Invalid JSON format" }), {
        status: 400,
        headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders
        }
      });
    }

    // 确定请求类型和语言
    const type = body.type || 'dream';
    const lang = body.lang || 'zh';
    const validLangs = ['zh', 'en', 'es', 'fr', 'ru', 'hi', 'pl', 'zh-TW']; 
    const normalizedLang = validLangs.includes(lang) ? lang : 'zh';

    // ---------------------------------------------------------
    // API Key 获取逻辑
    // ---------------------------------------------------------
    const apiKey = body.apiKey || env.GEMINI_API_KEY;

    if (!apiKey) {
      return new Response(JSON.stringify({ error: "Server Configuration Error: No API Key provided" }), {
        status: 500,
        headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders
        }
      });
    }

    // 构建提示词
    const languageNames = { 
        'zh': 'Chinese', 'zh-TW': 'Traditional Chinese', 
        'en': 'English', 'es': 'Spanish', 'fr': 'French', 
        'ru': 'Russian', 'hi': 'Hindi', 'pl': 'Polish' 
    };
    const targetLang = languageNames[normalizedLang] || 'Chinese';
    let promptText = "";

    if (type === 'symbol') {
      const { symbol } = body;
      if (!symbol || typeof symbol !== 'string' || symbol.trim() === '') {
        return new Response(JSON.stringify({ error: "Missing or invalid symbol keyword" }), {
          status: 400,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }

      promptText = `
        Interpret the dream symbol: "${symbol.trim()}".
        Return a raw JSON object (no markdown) with keys:
        {
            "psych": "Psychological meaning (1-2 sentences)",
            "trad": "Traditional/Folklore meaning (1-2 sentences)"
        }
        Response language: ${targetLang}.
      `.trim();
    } else {
      const { dream } = body;
      if (!dream || typeof dream !== 'string' || dream.trim() === '') {
        return new Response(JSON.stringify({ error: "Missing or invalid dream content" }), {
          status: 400,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }

      promptText = `
        You are a professional Jungian dream interpreter.
        Analyze this dream: "${dream.trim()}"
        Return a raw JSON object (no markdown) with keys:
        {
            "core_metaphor": "One sentence summary.",
            "emotions": "Emotional analysis.",
            "guidance": "Actionable life guidance.",
            "lucky_item": "A lucky color or item."
        }
        Response language: ${targetLang}.
      `.trim();
    }

    // ---------------------------------------------------------
    // 调用 Google Gemini API
    // 升级：使用 gemini-2.5-flash 并关闭 thinkingConfig 以提高速度
    // ---------------------------------------------------------
    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`;

    try {
      const geminiResponse = await fetchWithRetry(apiUrl, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-goog-api-key': apiKey
        },
        body: JSON.stringify({
          contents: [{ parts: [{ text: promptText }] }],
          generationConfig: { 
            responseMimeType: "application/json",
            // 关键优化：显式关闭思考功能，避免推理带来的额外延迟
            // 在 SDK 中对应 thinkingBudget: 0，在 REST API 中通常通过 includeThoughts: false 控制
            thinkingConfig: { includeThoughts: false } 
          }
        })
      });

      if (!geminiResponse.ok) {
        const errText = await geminiResponse.text().catch(() => 'No error details');
        console.error(`Gemini API Error (${geminiResponse.status}):`, errText);
        
        const status = (geminiResponse.status >= 400 && geminiResponse.status < 500) ? geminiResponse.status : 502;
        
        let errorMsg = `Upstream API Error: ${geminiResponse.status}`;
        if (geminiResponse.status === 400 && errText.includes('API_KEY')) {
            errorMsg = "API Key Invalid or Expired";
        }

        return new Response(JSON.stringify({ 
          error: errorMsg,
          details: errText
        }), {
          status: status,
          headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders
          }
        });
      }

      const data = await geminiResponse.json();
      const rawText = data.candidates?.[0]?.content?.parts?.[0]?.text?.trim();
      
      if (!rawText) {
        throw new Error("No valid response from Gemini API");
      }

      const cleanedText = rawText.replace(/```json/g, '').replace(/```/g, '').trim();

      try {
        JSON.parse(cleanedText);
      } catch (jsonError) {
        console.error("Invalid JSON from Gemini:", cleanedText);
        throw new Error("Received invalid response format from upstream API");
      }

      return new Response(cleanedText, {
        headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders
        }
      });
    } catch (fetchError) {
      console.error("API Request Error:", fetchError);
      return new Response(JSON.stringify({ 
        error: fetchError.message || "Failed to communicate with upstream API" 
      }), {
        status: 500,
        headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders
        }
      });
    }

  } catch (err) {
    console.error("Worker Error:", err);
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders
      }
    });
  }
}
