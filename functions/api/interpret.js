/**
 * Cloudflare Pages Function
 * 处理 /api/interpret 的 POST 请求
 * 功能：作为网关，处理“解梦”和“象征查询”两种请求
 * 更新：增加 CORS 支持；增加 API Key Body 优先逻辑；优化为 Header 鉴权
 * 修复：解决 404 错误，升级为 gemini-2.0-flash 模型 (根据用户提供的官方示例)
 */

// 定义通用的 CORS 头部
const corsHeaders = {
  'Access-Control-Allow-Origin': '*', // 允许所有来源
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

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
    // 优先从 env 获取，确保使用了 Cloudflare 托管的密钥
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
    // 修复：更新为 gemini-2.0-flash，解决 404 错误
    // 优化：使用 Header 传递 Key (X-goog-api-key)
    // ---------------------------------------------------------
    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`;

    try {
      const geminiResponse = await fetch(apiUrl, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-goog-api-key': apiKey // 使用 Header 鉴权
        },
        body: JSON.stringify({
          contents: [{ parts: [{ text: promptText }] }],
          generationConfig: { responseMimeType: "application/json" }
        }),
        timeout: 25000 
      });

      if (!geminiResponse.ok) {
        const errText = await geminiResponse.text().catch(() => 'No error details');
        console.error(`Gemini API Error (${geminiResponse.status}):`, errText);
        
        const status = (geminiResponse.status >= 400 && geminiResponse.status < 500) ? geminiResponse.status : 502;
        const errorMsg = `Upstream API Error: ${geminiResponse.status}`;

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
