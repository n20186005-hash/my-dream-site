/**
 * Cloudflare Pages Function
 * 处理 /api/interpret 的 POST 请求
 * 功能：作为网关，处理“解梦”和“象征查询”两种请求
 */
export async function onRequestPost(context) {
  try {
    const { request, env } = context;
    const body = await request.json();
    
    // 1. 确定请求类型 (默认为解梦)
    const type = body.type || 'dream'; 
    const lang = body.lang || 'zh';
    
    // 2. 获取 API Key (优先环境变量，其次硬编码备用)
    const apiKey = env.GEMINI_API_KEY || "AIzaSyCQbW5qLkdDvoWMdOb_poNe8Y-wBidE5rw";
    
    if (!apiKey) {
      return new Response(JSON.stringify({ error: "Server Configuration Error: Missing API Key" }), { 
        status: 500, 
        headers: { 'Content-Type': 'application/json' } 
      });
    }

    // 3. 根据类型构建 Prompt
    const languageNames = { 'zh': 'Chinese', 'en': 'English', 'es': 'Spanish', 'fr': 'French' };
    const targetLang = languageNames[lang] || 'Chinese';
    
    let promptText = "";

    if (type === 'symbol') {
        // --- 场景 A: 象征字典查询 ---
        const symbol = body.symbol;
        if (!symbol) throw new Error("Missing symbol keyword");
        
        promptText = `
            Interpret the dream symbol: "${symbol}".
            Return a raw JSON object (no markdown) with keys:
            {
                "psych": "Psychological meaning (1-2 sentences)",
                "trad": "Traditional/Folklore meaning (1-2 sentences)"
            }
            Response language: ${targetLang}.
        `;
    } else {
        // --- 场景 B: 梦境解析 (默认) ---
        const dream = body.dream;
        if (!dream) throw new Error("Missing dream content");

        promptText = `
          You are a professional Jungian dream interpreter.
          Analyze this dream: "${dream}"
          
          Return a raw JSON object (no markdown) with keys:
          {
              "core_metaphor": "One sentence summary.",
              "emotions": "Emotional analysis.",
              "guidance": "Actionable life guidance.",
              "lucky_item": "A lucky color or item."
          }
          Response language: ${targetLang}.
        `;
    }

    // 4. 调用 Google Gemini API
    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;

    const geminiResponse = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: promptText }] }],
        generationConfig: { responseMimeType: "application/json" }
      })
    });

    if (!geminiResponse.ok) {
      const errText = await geminiResponse.text();
      console.error(`Gemini API Error (${geminiResponse.status}):`, errText);
      throw new Error(`Upstream API Error: ${geminiResponse.status}`);
    }

    const data = await geminiResponse.json();
    let rawText = data.candidates?.[0]?.content?.parts?.[0]?.text;
    
    if (!rawText) throw new Error("No text returned from Gemini");

    // 清理 Markdown 格式
    rawText = rawText.replace(/```json/g, '').replace(/```/g, '').trim();

    return new Response(rawText, {
      headers: { 'Content-Type': 'application/json' }
    });

  } catch (err) {
    console.error("Worker Error:", err);
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
