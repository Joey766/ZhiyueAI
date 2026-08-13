const $ = (id) => document.getElementById(id);
const labels = {preferred_name:'Preferred Name',first_name:'First Name',last_name:'Last Name',full_name:'Full Name',email:'Email',phone:'Phone',location:'Location',linkedin:'LinkedIn',github:'GitHub',portfolio:'Portfolio',school:'School',degree:'Degree',major:'Major',gpa:'GPA',graduation_date:'Graduation Date',work_authorization:'Work Authorization',requires_sponsorship:'Sponsorship',willing_to_relocate:'Relocation',company:'Company',job_title:'Job Title',start_date:'Start Date',end_date:'End Date',responsibilities:'Responsibilities'};

async function aliases(){
  const response = await fetch(chrome.runtime.getURL('field_aliases.json'));
  if(!response.ok) throw Error('字段规则文件无法读取');
  return response.json();
}
function scanPage(dictionary, open){
  function classifyLocal(text){
    text=(text||'').toLowerCase().replace(/\s+/g,' ').trim();
    if(open.some(x=>text.includes(x))) return 'open_ended';
    for(const [key,terms] of Object.entries(dictionary)) if(terms.some(x=>text.includes(x))) return key;
    return 'unknown';
  }
  const candidates=[...document.querySelectorAll('input,textarea,select')].filter(el=>!['hidden','password'].includes((el.type||'').toLowerCase())&&!el.disabled);
  function classifyEvidence(...values){
    for(const value of values){
      if(!value) continue;
      const kind=classifyLocal(value);
      if(kind!=='unknown') return kind;
    }
    return 'unknown';
  }
  return candidates.map((el,index)=>{
    let label='';
    if(el.labels) label=[...el.labels].map(x=>x.innerText).join(' ');
    if(!label&&el.id){const x=document.querySelector(`label[for="${CSS.escape(el.id)}"]`);if(x)label=x.innerText}
    const ariaLabel=el.getAttribute('aria-label')||'';
    const placeholder=el.placeholder||'';
    const name=el.name||'';
    const nearby=el.closest('div,fieldset,li,section,form')?.innerText?.slice(0,500)||'';
    // Never merge parent-container text with stronger, field-specific evidence.
    const kind=classifyEvidence(label,ariaLabel,placeholder,name,nearby);
    return {id:index,label:label||ariaLabel||placeholder||name||'未命名字段',kind,type:el.tagName.toLowerCase()};
  });
}
function jobContext(){
  const nodes=[...document.querySelectorAll('h1,h2,h3,h4,strong')];
  const h=nodes.find(x=>/job description|responsibilities|岗位职责|职位描述/i.test(x.innerText||''));
  return {title:document.title,context:(h?.parentElement?.innerText||document.title).slice(0,5000)};
}
async function profile(token){const r=await fetch('http://127.0.0.1:8765/application-profile',{headers:{'X-Zhiyue-Token':token}});const j=await r.json();if(!r.ok)throw Error(j.error||'无法读取本机资料');return j.profile}
function value(p,k){if(p.personal?.[k]!==undefined)return p.personal[k];if(['school','degree','major','gpa'].includes(k))return p.education?.find(x=>x[k])?.[k]||'';if(k==='graduation_date')return p.application_info?.graduation_date||'';if(['work_authorization','requires_sponsorship','willing_to_relocate'].includes(k))return p.application_info?.[k]??'';if(['company','job_title','start_date','end_date','responsibilities'].includes(k))return p.experience?.find(x=>x[k])?.[k]||'';return ''}
async function copy(text){await navigator.clipboard.writeText(String(text));$('status').textContent='已复制';}
function render(fields,p,token){
  const root=$('results');root.innerHTML='';
  fields.forEach(f=>{const item=document.createElement('article');item.className='item';const title=document.createElement('strong');title.textContent=f.label;item.append(title);
    if(f.kind==='open_ended'){const msg=document.createElement('p');msg.textContent='这是一个开放题';item.append(msg);const b=document.createElement('button');b.textContent='AI 帮我准备回答';b.onclick=async()=>{b.disabled=true;$('status').textContent='正在准备草稿…';try{const [tab]=await chrome.tabs.query({active:true,currentWindow:true});const [ctx]=await chrome.scripting.executeScript({target:{tabId:tab.id},func:jobContext});const r=await fetch('http://127.0.0.1:8765/open-answer',{method:'POST',headers:{'Content-Type':'application/json','X-Zhiyue-Token':token},body:JSON.stringify({question:f.label,job_context:ctx.result.context+'\n'+ctx.result.title})});const j=await r.json();if(!r.ok)throw Error(j.error||'AI 暂不可用');msg.textContent=j.answer;const c=document.createElement('button');c.textContent='复制草稿';c.onclick=()=>copy(j.answer);item.append(c);$('status').textContent='草稿已生成，请自行核对'}catch(e){$('status').textContent='无法生成草稿：'+e.message}finally{b.disabled=false}};item.append(b)}
    else if(f.kind==='unknown'){const msg=document.createElement('p');msg.className='unknown';msg.textContent='⚠️ 未识别字段，请你确认';item.append(msg)}
    else{const v=value(p,f.kind);const msg=document.createElement('p');if(v===''||v===null){msg.className='missing';msg.textContent='⚠️ 当前资料中没有这个信息，请你确认'}else{msg.textContent=typeof v==='boolean'?(v?'是':'否'):String(v);const b=document.createElement('button');b.textContent='复制';b.onclick=()=>copy(msg.textContent);item.append(b)}item.append(msg)}root.append(item)});
}
async function run(){
  const token=$('token').value.trim();if(!token){$('status').textContent='请先输入本机访问密钥';return}
  await chrome.storage.local.set({zhiyueToken:token});$('status').textContent='正在识别当前申请表…';
  try{const [tab]=await chrome.tabs.query({active:true,currentWindow:true});const rules=await aliases();const [res]=await chrome.scripting.executeScript({target:{tabId:tab.id},func:scanPage,args:[rules.fields,rules.open_ended_terms]});const p=await profile(token);render(res.result,p,token);$('status').textContent=`已识别 ${res.result.length} 个字段`}
  catch(e){$('status').textContent='无法识别：'+e.message}
}
chrome.storage.local.get('zhiyueToken').then(x=>{$('token').value=x.zhiyueToken||''});$('scan').addEventListener('click',run);
