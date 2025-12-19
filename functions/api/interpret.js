/**
 * Cloudflare Pages Function
 * 处理 /api/interpret 的 POST 请求
 */
export async function onRequestPost(context) {
  try {
    const { request, env } = context;

    // 1. 获取前端传来的数据
    const body = await request.json();
    const { dream, lang } = body;

    // 简单验证
    if (!dream) {
      return new Response(JSON.stringify({ error: "请输入梦境内容" }), { 
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // 2. 获取 API Key
    // 优先使用环境变量，如果未设置则使用硬编码的备用 Key (修复用户反馈的问题)
    const apiKey = env.GEMINI_API_KEY || "AIzaSyCQbW5qLkdDvoWMdOb_poNe8Y-wBidE5rw";
    
    if (!apiKey) {
      return new Response(JSON.stringify({ error: "服务器配置错误: 未找到 API Key" }), { 
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // 3. 构建 Prompt
    const languageNames = {
      'zh': 'Chinese (Simplified)',
      'en': 'English',
      'es': 'Spanish',
      'fr': 'French'
    };
    const targetLang = languageNames[lang] || 'Chinese (Simplified)';

    const promptText = `
      You are a professional Jungian dream interpreter and therapist.
      The user has shared the following dream:
      "${dream}"
      
      Please analyze this dream and return a raw JSON object (no markdown, no code blocks) with the following structure.
      Ensure the content is written in the following language: ${targetLang}.
      
      Keep the tone gentle, mysterious, but professional.

      JSON Structure:
      {
          "core_metaphor": "One sentence summary of the core metaphor.",
          "emotions": "Analysis of emotions (e.g., Anxiety 30%, Hope 70%).",
          "guidance": "Warm, actionable life guidance based on the dream.",
          "lucky_item": "A suggested lucky color or item (e.g., 'Moonstone' or 'Pale Blue')."
      }
    `;

    // 4. 调用 Google Gemini API
    // 使用 gemini-1.5-flash 模型 (目前最稳定，2.0 可能处于预览状态)
    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;

    const geminiResponse = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: promptText }] }],
        generationConfig: {
          responseMimeType: "application/json"
        }
      })
    });

    if (!geminiResponse.ok) {
      const errorText = await geminiResponse.text();
      console.error(`Gemini API Error: ${geminiResponse.status}`, errorText);
      throw new Error(`Gemini API Error: ${geminiResponse.status}`);
    }

    // 5. 处理并返回结果
    const data = await geminiResponse.json();
    
    if (!data.candidates || data.candidates.length === 0) {
        throw new Error("Gemini returned no candidates");
    }

    let rawText = data.candidates[0].content.parts[0].text;
    
    // 清理可能存在的 Markdown 标记
    rawText = rawText.replace(/```json/g, '').replace(/```/g, '').trim();

    return new Response(rawText, {
      headers: { 'Content-Type': 'application/json' }
    });

  } catch (err) {
    console.error("Function Error:", err);
    return new Response(JSON.stringify({ error: err.message || "Internal Server Error" }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
