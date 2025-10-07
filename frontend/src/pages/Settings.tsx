import { useEffect, useState } from 'react'
import { Auth, Admin, Diagnostics } from '../api'

export default function Settings(){
  const [status, setStatus] = useState<any>({})
  const today = new Date().toISOString().slice(0,10)
  const [date, setDate] = useState<string>(today)
  useEffect(()=>{ Auth.naverStatus().then(setStatus) }, [])
  const login = async ()=>{
    const url = await Auth.naverLoginUrl();
    window.location.href = url
  }
  const [ai, setAi] = useState<any>(null)
  const checkAI = async ()=>{
    const r = await Diagnostics.ai();
    setAi(r)
    if(!r.ok){
      alert('AI 연결 실패: ' + (r.reason || '원인 불명'))
    }
  }
  const [aiCfg, setAiCfg] = useState<any>({})
  useEffect(()=>{ Admin.getAIConfig().then(setAiCfg) }, [])
  const saveAi = async ()=>{
    const r = await Admin.setAIConfig(aiCfg)
    setAiCfg(r)
    alert('AI 설정 저장 완료')
  }
  return (
    <div className="row">
      <div className="card" style={{gridColumn:'span 6'}}>
        <h3>네이버 블로그 연결</h3>
        <div>{status.connected? '연결됨 ✅' : '미연결 ⚠️'}</div>
        {!status.connected && (<button className="btn" onClick={login}>네이버 로그인</button>)}
        {status.expires_at && (<div>만료: {status.expires_at}</div>)}
      </div>
      <div className="card" style={{gridColumn:'span 6'}}>
        <h3>모델/예산 안내</h3>
        <p>월 예산은 서버 .env의 OPENAI_MONTHLY_MAX_USD로 관리됩니다.</p>
        <div style={{display:'flex', gap:8, alignItems:'center'}}>
          <button className="btn" onClick={checkAI}>AI 연결 확인</button>
          {ai && (
            <div>
              <div>상태: {ai.ok? 'OK' : 'FAIL'}</div>
              <div className="mono">키 존재: {String(ai.has_api_key)}</div>
              {ai.total_tokens!=null && (<div className="mono">토큰: {ai.total_tokens}</div>)}
              {ai.reason && (<div className="mono">사유: {ai.reason}</div>)}
            </div>
          )}
        </div>
      </div>
      <div className="card" style={{gridColumn:'span 12'}}>
        <h3>AI 모델 설정(gpt | gemini)</h3>
        <div className="row">
          <div className="card" style={{gridColumn:'span 6'}}>
            <label>Provider
              <select className="input" value={aiCfg.ai_provider||'gpt'} onChange={e=>setAiCfg((s:any)=>({...s, ai_provider:e.target.value}))}>
                <option value="gpt">gpt (OpenAI)</option>
                <option value="gemini">gemini (Google)</option>
              </select>
            </label>
            <div style={{marginTop:8}}>
              <label>OpenAI small
                <input className="input" value={aiCfg.openai_model_small||''} onChange={e=>setAiCfg((s:any)=>({...s, openai_model_small:e.target.value}))} />
              </label>
            </div>
            <div style={{marginTop:8}}>
              <label>OpenAI writer
                <input className="input" value={aiCfg.openai_model_writer||''} onChange={e=>setAiCfg((s:any)=>({...s, openai_model_writer:e.target.value}))} />
              </label>
            </div>
          </div>
          <div className="card" style={{gridColumn:'span 6'}}>
            <div>
              <label>Gemini small
                <input className="input" value={aiCfg.gemini_model_small||''} onChange={e=>setAiCfg((s:any)=>({...s, gemini_model_small:e.target.value}))} />
              </label>
            </div>
            <div style={{marginTop:8}}>
              <label>Gemini writer
                <input className="input" value={aiCfg.gemini_model_writer||''} onChange={e=>setAiCfg((s:any)=>({...s, gemini_model_writer:e.target.value}))} />
              </label>
            </div>
            <div style={{marginTop:8}}>
              <label>Gemini Safety
                <select className="input" value={aiCfg.gemini_safety||'low'} onChange={e=>setAiCfg((s:any)=>({...s, gemini_safety:e.target.value}))}>
                  <option value="default">default (medium)</option>
                  <option value="low">low (only high)</option>
                  <option value="none">none (no blocking)</option>
                </select>
              </label>
            </div>
          </div>
        </div>
        <button className="btn" onClick={saveAi}>AI 설정 저장</button>
        <p style={{marginTop:8}}>주의: API 키는 서버 .env에서 설정합니다(OPENAI_API_KEY, GEMINI_API_KEY).</p>
      </div>
      <div className="card" style={{gridColumn:'span 12', borderColor:'#5b1d1d'}}>
        <h3>Danger Zone (데이터 정리)</h3>
        <div style={{display:'flex', gap:12, alignItems:'center', marginBottom:8}}>
          <input className="input" type="date" value={date} onChange={e=>setDate(e.target.value)} style={{maxWidth:220}} />
          <button className="btn secondary" onClick={async()=>{
            if(!confirm(`[${date}] 키워드 및 관련 데이터 삭제?`)) return
            await Admin.deleteKeywords(date)
            alert('삭제 완료')
          }}>해당 날짜 키워드 삭제</button>
          <button className="btn secondary" onClick={async()=>{
            if(!confirm('모든 키워드/후보/초안 데이터를 삭제하시겠습니까? (되돌릴 수 없음)')) return
            await Admin.deleteKeywords()
            alert('전체 키워드 관련 삭제 완료')
          }}>키워드 전체 삭제</button>
          <button className="btn" style={{background:'#7a2626'}} onClick={async()=>{
            if(!confirm('DB 초기화(drop & create) 진행합니까? (모든 데이터 삭제)')) return
            await Admin.resetDb()
            alert('DB가 초기화되었습니다')
          }}>DB 초기화</button>
        </div>
        <div>
          <button className="btn secondary" onClick={async()=>{
            if(!confirm(`[${date}] 키워드 중복 정리(동일 text는 최신만 유지) 진행합니까?`)) return
            await Admin.dedupKeywords(date)
            alert('중복 정리 완료')
          }}>해당 날짜 키워드 중복 정리</button>
        </div>
      </div>
    </div>
  )
}
