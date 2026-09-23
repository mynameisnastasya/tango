'use client'

import { FormEvent, useEffect, useMemo, useState } from 'react'
import {
  ArrowLeft, BadgeCheck, Download, Filter, KeyRound, LogOut, Plus, RefreshCw,
  Search, Settings2, Users, UserCheck, Radio, Target, Save
} from 'lucide-react'

type Application = {
  id:string; created_at:string; name:string; country:string; languages:string;
  telegram:string; whatsapp:string; instagram:string; platform:string; experience:string;
  username:string; referral_code:string; hours_per_week:string; message:string;
  status:string; source:string;
}
type Referral = {
  id?:string; code:string; recruiter:string; market:string; onboarding_bonus:string; active:boolean;
}
type Settings = {
  welcome_bonus:string; milestone_title:string; milestone_reward:string;
  telegram_url:string; whatsapp_url:string; instagram_url:string; email:string;
  faq_en?:unknown; faq_ru?:unknown;
}

const statuses = ['New','Contacted','Approved','Rejected','Active','FTR Completed']
const defaultSettings:Settings = {
  welcome_bonus:'4,000–5,000 coins', milestone_title:'100,000 Diamond Milestone',
  milestone_reward:'Additional broadcaster reward may be available.',
  telegram_url:'', whatsapp_url:'', instagram_url:'', email:''
}

function csvCell(v:unknown){return `"${String(v ?? '').replace(/"/g,'""')}"`}

export default function AdminPage(){
  const [key,setKey]=useState('')
  const [logged,setLogged]=useState(false)
  const [apps,setApps]=useState<Application[]>([])
  const [refs,setRefs]=useState<Referral[]>([])
  const [settings,setSettings]=useState<Settings>(defaultSettings)
  const [search,setSearch]=useState('')
  const [country,setCountry]=useState('All')
  const [status,setStatus]=useState('All')
  const [recruiter,setRecruiter]=useState('All')
  const [tab,setTab]=useState<'applications'|'referrals'|'settings'>('applications')
  const [loading,setLoading]=useState(false)
  const [message,setMessage]=useState('')
  const [newRef,setNewRef]=useState<Referral>({code:'',recruiter:'',market:'International',onboarding_bonus:'',active:true})
  const [faqEn,setFaqEn]=useState('')
  const [faqRu,setFaqRu]=useState('')

  useEffect(()=>{
    const saved=sessionStorage.getItem('abhi_admin_key')
    if(saved){setKey(saved); login(saved)}
  // eslint-disable-next-line react-hooks/exhaustive-deps
  },[])

  async function login(adminKey=key){
    setLoading(true); setMessage('')
    try{
      const headers={'x-admin-key':adminKey}
      const [a,r,s]=await Promise.all([
        fetch('/api/applications',{headers}),
        fetch('/api/referrals',{headers}),
        fetch('/api/settings')
      ])
      if(a.status===401 || r.status===401) throw new Error('Wrong admin key')
      let appRows:Application[]=[]
      if(a.ok) appRows=await a.json()
      else appRows=JSON.parse(localStorage.getItem('abhi_demo_applications')||'[]')
      const refRows=r.ok?await r.json():[{code:'KCu4ZY',recruiter:'ABHIGREEN Manager',market:'International',onboarding_bonus:'Current onboarding bonus confirmed by manager',active:true}]
      const settingsRows=s.ok?await s.json():defaultSettings
      setApps(appRows); setRefs(refRows); setSettings({...defaultSettings,...settingsRows})
      setFaqEn(JSON.stringify(settingsRows.faq_en||[],null,2))
      setFaqRu(JSON.stringify(settingsRows.faq_ru||[],null,2))
      sessionStorage.setItem('abhi_admin_key',adminKey)
      setLogged(true)
    }catch(e){setMessage(e instanceof Error?e.message:'Could not sign in')}
    finally{setLoading(false)}
  }

  function logout(){sessionStorage.removeItem('abhi_admin_key');setLogged(false);setKey('')}

  async function refresh(){
    if(!logged)return
    setLoading(true)
    try{
      const headers={'x-admin-key':key}
      const [a,r,s]=await Promise.all([fetch('/api/applications',{headers}),fetch('/api/referrals',{headers}),fetch('/api/settings')])
      if(a.ok)setApps(await a.json())
      else setApps(JSON.parse(localStorage.getItem('abhi_demo_applications')||'[]'))
      if(r.ok)setRefs(await r.json())
      if(s.ok){const x=await s.json();setSettings({...defaultSettings,...x});setFaqEn(JSON.stringify(x.faq_en||[],null,2));setFaqRu(JSON.stringify(x.faq_ru||[],null,2))}
    }finally{setLoading(false)}
  }

  async function updateStatus(id:string,next:string){
    setApps(v=>v.map(x=>x.id===id?{...x,status:next}:x))
    const res=await fetch('/api/applications',{method:'PATCH',headers:{'Content-Type':'application/json','x-admin-key':key},body:JSON.stringify({id,status:next})})
    if(!res.ok){
      const demo=JSON.parse(localStorage.getItem('abhi_demo_applications')||'[]').map((x:Application)=>x.id===id?{...x,status:next}:x)
      localStorage.setItem('abhi_demo_applications',JSON.stringify(demo))
    }
  }

  async function addReferral(e:FormEvent){
    e.preventDefault(); setMessage('')
    const res=await fetch('/api/referrals',{method:'POST',headers:{'Content-Type':'application/json','x-admin-key':key},body:JSON.stringify(newRef)})
    if(res.ok){const row=await res.json();setRefs(v=>[row,...v.filter(x=>x.code!==row.code)]);setNewRef({code:'',recruiter:'',market:'International',onboarding_bonus:'',active:true});setMessage('Referral saved.')}
    else{
      setRefs(v=>[newRef,...v.filter(x=>x.code!==newRef.code)])
      setNewRef({code:'',recruiter:'',market:'International',onboarding_bonus:'',active:true})
      setMessage('Saved in dashboard demo mode. Configure Supabase for shared persistence.')
    }
  }

  async function saveSettings(){
    setMessage('')
    let faq_en:unknown=[];let faq_ru:unknown=[]
    try{faq_en=faqEn?JSON.parse(faqEn):[]}catch{setMessage('FAQ EN must be valid JSON.');return}
    try{faq_ru=faqRu?JSON.parse(faqRu):[]}catch{setMessage('FAQ RU must be valid JSON.');return}
    const payload={...settings,faq_en,faq_ru}
    const res=await fetch('/api/settings',{method:'PUT',headers:{'Content-Type':'application/json','x-admin-key':key},body:JSON.stringify(payload)})
    setMessage(res.ok?'Settings saved.':'Backend is not configured yet. Add Supabase environment variables to save globally.')
  }

  const countries=useMemo(()=>['All',...Array.from(new Set(apps.map(x=>x.country).filter(Boolean))).sort()], [apps])
  const recruiters=useMemo(()=>['All',...Array.from(new Set(refs.map(x=>x.recruiter).filter(Boolean))).sort()], [refs])
  const refOwner=(code:string)=>refs.find(r=>r.code===code)?.recruiter||'Unassigned'
  const filtered=useMemo(()=>apps.filter(a=>{
    const hay=[a.name,a.country,a.telegram,a.instagram,a.platform,a.referral_code].join(' ').toLowerCase()
    return (!search||hay.includes(search.toLowerCase())) && (country==='All'||a.country===country) && (status==='All'||a.status===status) && (recruiter==='All'||refOwner(a.referral_code)===recruiter)
  }),[apps,search,country,status,recruiter,refs])

  const metrics=useMemo(()=>({
    applications:apps.length,
    approved:apps.filter(x=>['Approved','Active','FTR Completed'].includes(x.status)).length,
    active:apps.filter(x=>['Active','FTR Completed'].includes(x.status)).length,
    ftr:apps.filter(x=>x.status==='FTR Completed').length,
  }),[apps])

  const refAnalytics=useMemo(()=>refs.map(r=>{
    const rows=apps.filter(a=>a.referral_code===r.code)
    const approved=rows.filter(a=>['Approved','Active','FTR Completed'].includes(a.status)).length
    const active=rows.filter(a=>['Active','FTR Completed'].includes(a.status)).length
    const ftr=rows.filter(a=>a.status==='FTR Completed').length
    return {...r,applications:rows.length,approved,active,ftr,conversion:rows.length?Math.round(approved/rows.length*100):0}
  }),[refs,apps])

  function exportCsv(){
    const headers=['created_at','name','country','languages','telegram','whatsapp','instagram','platform','username','referral_code','recruiter','hours_per_week','status','message','source']
    const rows=filtered.map(a=>[a.created_at,a.name,a.country,a.languages,a.telegram,a.whatsapp,a.instagram,a.platform,a.username,a.referral_code,refOwner(a.referral_code),a.hours_per_week,a.status,a.message,a.source])
    const csv=[headers.map(csvCell).join(','),...rows.map(r=>r.map(csvCell).join(','))].join('\n')
    const blob=new Blob([csv],{type:'text/csv;charset=utf-8;'})
    const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=`abhi-applications-${new Date().toISOString().slice(0,10)}.csv`;link.click();URL.revokeObjectURL(url)
  }

  if(!logged)return <main className="admin-login">
    <a href="/" className="admin-back"><ArrowLeft size={16}/> Back to website</a>
    <div className="login-card">
      <div className="brand"><span className="brand-mark">A</span><span><b>ABHIGREEN</b></span></div>
      <KeyRound size={30}/>
      <h1>Agency Admin</h1><p>Enter the ADMIN_KEY configured in your deployment environment.</p>
      <input type="password" value={key} onChange={e=>setKey(e.target.value)} onKeyDown={e=>e.key==='Enter'&&login()} placeholder="Admin key"/>
      <button className="button gold" onClick={()=>login()} disabled={loading}>{loading?'Checking...':'Open Dashboard'}</button>
      {message&&<div className="admin-message">{message}</div>}
    </div>
  </main>

  return <main className="admin-root">
    <aside className="admin-sidebar">
      <div className="brand"><span className="brand-mark">A</span><span><b>ABHIGREEN</b></span></div>
      <nav>
        <button className={tab==='applications'?'active':''} onClick={()=>setTab('applications')}><Users/>Applications</button>
        <button className={tab==='referrals'?'active':''} onClick={()=>setTab('referrals')}><Target/>Referral Codes</button>
        <button className={tab==='settings'?'active':''} onClick={()=>setTab('settings')}><Settings2/>Settings</button>
      </nav>
      <div className="sidebar-bottom"><a href="/"><ArrowLeft/>Website</a><button onClick={logout}><LogOut/>Log out</button></div>
    </aside>

    <section className="admin-main">
      <header className="admin-topbar">
        <div><small>ABHIGREEN</small><h1>{tab==='applications'?'Applicants':tab==='referrals'?'Referral Performance':'Agency Settings'}</h1></div>
        <button className="icon-button" onClick={refresh} title="Refresh"><RefreshCw className={loading?'spin':''}/></button>
      </header>

      {tab==='applications'&&<>
        <div className="metric-grid">
          <div><span><Users/></span><small>Applications</small><b>{metrics.applications}</b></div>
          <div><span><UserCheck/></span><small>Approved</small><b>{metrics.approved}</b></div>
          <div><span><Radio/></span><small>Active</small><b>{metrics.active}</b></div>
          <div><span><BadgeCheck/></span><small>FTR Completed</small><b>{metrics.ftr}</b></div>
        </div>
        <div className="admin-panel">
          <div className="toolbar">
            <label className="search-box"><Search/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search applicants"/></label>
            <label><Filter/><select value={country} onChange={e=>setCountry(e.target.value)}>{countries.map(x=><option key={x}>{x}</option>)}</select></label>
            <label><select value={recruiter} onChange={e=>setRecruiter(e.target.value)}>{recruiters.map(x=><option key={x}>{x}</option>)}</select></label>
            <label><select value={status} onChange={e=>setStatus(e.target.value)}>{['All',...statuses].map(x=><option key={x}>{x}</option>)}</select></label>
            <button className="button ghost admin-export" onClick={exportCsv}><Download/>Export CSV</button>
          </div>
          <div className="table-wrap">
            <table><thead><tr><th>Applicant</th><th>Country</th><th>Contact</th><th>Platform</th><th>Referral</th><th>Hours</th><th>Status</th><th>Date</th></tr></thead>
            <tbody>{filtered.map(a=><tr key={a.id}>
              <td><b>{a.name}</b><small>{a.languages||'—'}</small></td><td>{a.country}</td>
              <td><span className="stack">{a.telegram||a.whatsapp||a.instagram||'—'}</span></td>
              <td>{a.platform||'—'}<small>{a.username}</small></td>
              <td><b>{a.referral_code||'Direct'}</b><small>{refOwner(a.referral_code)}</small></td>
              <td>{a.hours_per_week||'—'}</td>
              <td><select className={'status-select status-'+a.status.toLowerCase().replaceAll(' ','-')} value={a.status} onChange={e=>updateStatus(a.id,e.target.value)}>{statuses.map(x=><option key={x}>{x}</option>)}</select></td>
              <td>{new Date(a.created_at).toLocaleDateString()}</td>
            </tr>)}</tbody></table>
            {!filtered.length&&<div className="empty-state">No applications match these filters.</div>}
          </div>
        </div>
      </>}

      {tab==='referrals'&&<>
        <div className="admin-panel referral-admin-form">
          <div><h2>Create / update referral code</h2><p>Use separate codes for recruiters, countries and campaigns.</p></div>
          <form onSubmit={addReferral}>
            <input required placeholder="Code" value={newRef.code} onChange={e=>setNewRef({...newRef,code:e.target.value})}/>
            <input required placeholder="Recruiter / manager" value={newRef.recruiter} onChange={e=>setNewRef({...newRef,recruiter:e.target.value})}/>
            <input placeholder="Market / country" value={newRef.market} onChange={e=>setNewRef({...newRef,market:e.target.value})}/>
            <input placeholder="Onboarding bonus description" value={newRef.onboarding_bonus} onChange={e=>setNewRef({...newRef,onboarding_bonus:e.target.value})}/>
            <button className="button gold"><Plus/>Save code</button>
          </form>
        </div>
        <div className="admin-panel">
          <div className="table-wrap"><table><thead><tr><th>Code</th><th>Recruiter</th><th>Market</th><th>Applications</th><th>Approved</th><th>Active</th><th>FTR</th><th>Approval conversion</th></tr></thead>
          <tbody>{refAnalytics.map(r=><tr key={r.code}><td><b>{r.code}</b></td><td>{r.recruiter}</td><td>{r.market}</td><td>{r.applications}</td><td>{r.approved}</td><td>{r.active}</td><td>{r.ftr}</td><td><b>{r.conversion}%</b></td></tr>)}</tbody></table></div>
        </div>
      </>}

      {tab==='settings'&&<div className="settings-grid">
        <div className="admin-panel settings-card">
          <h2>Bonuses & milestones</h2>
          <label>Welcome bonus<input value={settings.welcome_bonus} onChange={e=>setSettings({...settings,welcome_bonus:e.target.value})}/></label>
          <label>Milestone title<input value={settings.milestone_title} onChange={e=>setSettings({...settings,milestone_title:e.target.value})}/></label>
          <label>Milestone reward<textarea rows={3} value={settings.milestone_reward} onChange={e=>setSettings({...settings,milestone_reward:e.target.value})}/></label>
        </div>
        <div className="admin-panel settings-card">
          <h2>Contacts</h2>
          <label>Telegram URL<input value={settings.telegram_url} onChange={e=>setSettings({...settings,telegram_url:e.target.value})} placeholder="https://t.me/..."/></label>
          <label>WhatsApp URL<input value={settings.whatsapp_url} onChange={e=>setSettings({...settings,whatsapp_url:e.target.value})} placeholder="https://wa.me/..."/></label>
          <label>Instagram URL<input value={settings.instagram_url} onChange={e=>setSettings({...settings,instagram_url:e.target.value})} placeholder="https://instagram.com/..."/></label>
          <label>Email<input value={settings.email} onChange={e=>setSettings({...settings,email:e.target.value})}/></label>
        </div>
        <div className="admin-panel settings-card full-card">
          <h2>FAQ content</h2><p>Optional override. Use JSON arrays in the format: <code>[[&quot;Question&quot;,&quot;Answer&quot;]]</code>. Empty arrays keep the built-in FAQ.</p>
          <div className="faq-editors"><label>English FAQ<textarea rows={10} value={faqEn} onChange={e=>setFaqEn(e.target.value)}/></label><label>Russian FAQ<textarea rows={10} value={faqRu} onChange={e=>setFaqRu(e.target.value)}/></label></div>
        </div>
        <div className="settings-save"><button className="button gold" onClick={saveSettings}><Save/>Save settings</button>{message&&<span>{message}</span>}</div>
      </div>}
    </section>
  </main>
}
