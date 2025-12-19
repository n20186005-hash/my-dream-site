/**
 * Cloudflare Pages Function
 * 处理 /api/interpret 的 POST 请求
 * 功能：作为网关，处理“解梦”和“象征查询”两种请求
 */
export async function onRequestPost(context) {
  try {
    const { request, env } = context;
    
    // 验证请求方法和内容类型
    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ error: "Method not allowed" }), {
        status: 405,
        headers: { 'Content-Type': 'application/json', 'Allow': 'POST' }
      });
    }

    if (!request.headers.get('Content-Type')?.includes('application/json')) {
      return new Response(JSON.stringify({ error: "Unsupported Media Type. Use application/json" }), {
        status: 415,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // 解析请求体
    let body;
    try {
      body = await request.json();
    } catch (parseError) {
      return new Response(JSON.stringify({ error: "Invalid JSON format" }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // 确定请求类型和语言
    const type = body.type || 'dream';
    const lang = body.lang || 'zh';
    const validLangs = ['zh', 'en', 'es', 'fr'];
    const normalizedLang = validLangs.includes(lang) ? lang : 'zh';

    // 获取 API Key
    const apiKey = env.GEMINI_API_KEY || "AIzaSyCQbW5qLkdDvoWMdOb_poNe8Y-wBidE5rw";
    if (!apiKey) {
      return new Response(JSON.stringify({ error: "Server Configuration Error: Missing API Key" }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // 构建提示词
    const languageNames = { 'zh': 'Chinese', 'en': 'English', 'es': 'Spanish', 'fr': 'French' };
    const targetLang = languageNames[normalizedLang];
    let promptText = "";

    if (type === 'symbol') {
      // 象征字典查询
      const { symbol } = body;
      if (!symbol || typeof symbol !== 'string' || symbol.trim() === '') {
        return new Response(JSON.stringify({ error: "Missing or invalid symbol keyword" }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' }
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
      // 梦境解析 (默认)
      const { dream } = body;
      if (!dream || typeof dream !== 'string' || dream.trim() === '') {
        return new Response(JSON.stringify({ error: "Missing or invalid dream content" }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' }
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

    // 调用 Google Gemini API
    const apiUrl = `https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=${apiKey}`;

    try {
      const geminiResponse = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: promptText }] }],
          generationConfig: { responseMimeType: "application/json" }
        }),
        timeout: 15000 // 15秒超时
      });

      if (!geminiResponse.ok) {
        const errText = await geminiResponse.text().catch(() => 'No error details');
        console.error(`Gemini API Error (${geminiResponse.status}):`, errText);
        return new Response(JSON.stringify({ 
          error: `Upstream API Error: ${geminiResponse.status}`,
          details: geminiResponse.status < 500 ? errText : undefined
        }), {
          status: geminiResponse.status < 500 ? 400 : 502,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      const data = await geminiResponse.json();
      const rawText = data.candidates?.[0]?.content?.parts?.[0]?.text?.trim();
      
      if (!rawText) {
        throw new Error("No valid response from Gemini API");
      }

      // 清理可能的Markdown格式
      const cleanedText = rawText.replace(/```json/g, '').replace(/```/g, '').trim();

      // 验证返回的JSON格式
      try {
        JSON.parse(cleanedText);
      } catch (jsonError) {
        console.error("Invalid JSON from Gemini:", cleanedText);
        throw new Error("Received invalid response format from upstream API");
      }

      return new Response(cleanedText, {
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (fetchError) {
      console.error("API Request Error:", fetchError);
      return new Response(JSON.stringify({ 
        error: fetchError.message || "Failed to communicate with upstream API" 
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }

  } catch (err) {
    console.error("Worker Error:", err);
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
