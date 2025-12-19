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

    // 2. 获取环境变量中的 API Key (安全！)
    // 请务必在 Cloudflare Pages 后台设置 GEMINI_API_KEY
    const apiKey = env.GEMINI_API_KEY;
    
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
    // 修正点：使用上面获取的 apiKey 变量，而不是硬编码
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
      // 这里可以打印日志到 Cloudflare 后台以便调试
      console.error(`Gemini API Error: ${geminiResponse.status}`, errorText);
      throw new Error(`Gemini API Error: ${geminiResponse.status}`);
    }

    // 5. 处理并返回结果
    const data = await geminiResponse.json();
    
    // 安全检查：确保 API 返回了有效的 candidates
    if (!data.candidates || data.candidates.length === 0) {
        throw new Error("Gemini returned no candidates");
    }

    let rawText = data.candidates[0].content.parts[0].text;
    
    // 清理可能存在的 Markdown 标记 (尽管我们在 prompt 里要求了 raw JSON)
    rawText = rawText.replace(/```json/g, '').replace(/```/g, '').trim();

    return new Response(rawText, {
      headers: { 'Content-Type': 'application/json' }
    });

  } catch (err) {
    console.error("Backend Error:", err);
    // 返回给前端一个通用的错误信息，避免暴露过多系统细节
    return new Response(JSON.stringify({ error: "解析服务暂时不可用，请检查 API Key 配置或稍后再试。" }), { 
      status: 500,
      headers: { 'Content-Type': 'application/json' } 
    });
  }
}
