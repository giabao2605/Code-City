// Code City governance guard. Node.js standard library only; no npm install required.
// This checks tracking consistency, NOT correctness of product code or validity of external evidence.
import { readFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const validate = function validate(master,progress,readme,requiredFiles) {
  const errors=[];
  const check=(condition,message)=>{if(!condition)errors.push(message)};
  const version=(master.match(/\*\*Phiên bản:\*\* (\d+\.\d+\.\d+)/)||[])[1];
  const metadata={};
  for(const m of progress.matchAll(/^- \*\*(Plan version|Phase|Current gate|Next task|Updated \(UTC\)):\*\* `([^`]+)`/gm))metadata[m[1]]=m[2];
  check(!!version,"Missing Master Plan version");
  check(metadata["Plan version"]===version,"PROGRESS Plan version differs from MASTER_PLAN");
  check(/^\d{4}-\d{2}-\d{2}$/.test(metadata["Updated (UTC)"]||""),"Invalid progress update date");
  const planTasks=[];const planGates=[];let gate=null;
  const section=master.split("## 13. Lộ trình")[1]?.split("## 14. Quy tắc")[0]||"";
  for(const line of section.split(/\r?\n/)){
    const g=line.match(/^### (G[0-8]) —/);
    if(g){gate=g[1];planGates.push(gate)}
    const t=line.match(/^- \[ \] \*\*(CC-\d{3})\*\* (.+)$/);
    if(t)planTasks.push({id:t[1],gate,title:t[2]});
  }
  const acceptanceIds=[...master.matchAll(/^\| (A\d{2}) \|/gm)].map(x=>x[1]);
  check(planGates.length===9 && new Set(planGates).size===9,"Expected 9 distinct G0-G8 milestones");
  check(planTasks.length===43 && new Set(planTasks.map(x=>x.id)).size===43,"Expected 43 unique CC tasks in Master Plan; change requires governance review");
  check(acceptanceIds.length===18 && new Set(acceptanceIds).size===18,"Expected 18 unique acceptance IDs in Master Plan");
  function table(title){
    const section=progress.split(title)[1]?.split(/\n## \d+\./)[0]||"";
    const rows=section.split(/\r?\n/).filter(x=>x.startsWith("|"));
    check(rows.length>=2,"Missing table "+title);
    return rows.slice(2).map(line=>line.split("|").slice(1,-1).map(cell=>cell.trim()));
  }
  const gateRows=table("## 2. Gate tracker");
  const taskRows=table("## 3. Task tracker");
  const accRows=table("## 4. Acceptance tracker");
  const keys=(rows)=>rows.map(row=>row[0]);
  const exactSet=(actual,expected,name)=>{
    const a=new Set(actual),b=new Set(expected);
    check(actual.length===expected.length&&a.size===expected.length&&expected.every(x=>a.has(x)),name+" ID mismatch/duplicate/missing");
  };
  exactSet(keys(gateRows),planGates,"Gate tracker");
  exactSet(keys(taskRows),planTasks.map(t=>t.id),"Task tracker");
  exactSet(keys(accRows),acceptanceIds,"Acceptance tracker");
  const current=metadata["Current gate"],next=metadata["Next task"],phase=metadata.Phase;
  const currentIndex=planGates.indexOf(current);
  check(currentIndex!==-1,"Current gate not in Master Plan");
  check(["PLANNING_ONLY","IN_DEVELOPMENT","RELEASE_CANDIDATE","RELEASED"].includes(phase),"Invalid project phase");
  const evidenceOK=(e)=>/^https:\/\/github\.com\/giabao2605\/Code-City\/(pull|commit|actions\/runs)\/[A-Za-z0-9_-]+/.test(e||"");
  const gateStatus={};
  for(const row of gateRows){
    check(row.length===4,"Gate row should have 4 columns: "+row[0]);
    const [id,status,evidence]=row;gateStatus[id]=status;
    check(["LOCKED","READY","IN_PROGRESS","BLOCKED","VERIFIED"].includes(status),"Invalid gate status "+id);
    const idx=planGates.indexOf(id);
    if(idx<currentIndex)check(status==="VERIFIED","Previous gate must be VERIFIED: "+id);
    if(idx===currentIndex)check(["READY","IN_PROGRESS","BLOCKED"].includes(status),"Current gate must be READY/IN_PROGRESS/BLOCKED: "+id);
    if(idx>currentIndex)check(status==="LOCKED","Future gate must be LOCKED: "+id);
    if(status==="VERIFIED")check(evidenceOK(evidence),"VERIFIED gate requires GitHub exit evidence: "+id);
  }
  const taskStatus={};
  for(const row of taskRows){
    check(row.length===6,"Task row should have 6 columns: "+row[0]);
    const [id,g,statusTitle,status,evidence,note]=row;taskStatus[id]=status;
    const canonical=planTasks.find(x=>x.id===id);
    if(canonical){
      check(g===canonical.gate,"Task assigned to wrong gate: "+id);
      check(statusTitle===canonical.title.replace(/\|/g,"/").replace(/\s+/g," ").trim(),"Task title differs from Master Plan: "+id);
    }
    check(["TODO","IN_PROGRESS","BLOCKED","VERIFIED"].includes(status),"Invalid task status: "+id);
    const idx=planGates.indexOf(g);
    if(idx>currentIndex)check(status==="TODO","Future task started before gate: "+id);
    if(idx<currentIndex)check(status==="VERIFIED","Earlier task not VERIFIED: "+id);
    if(status==="VERIFIED"){
      check(evidenceOK(evidence),"VERIFIED task requires GitHub evidence: "+id);
      check(note && note!=="-" && note!=="Chưa bắt đầu","VERIFIED task requires test/DoD note: "+id);
    }
  }
  for(const row of gateRows){
    const [id,status]=row;
    if(status==="VERIFIED")check(planTasks.filter(x=>x.gate===id).every(x=>taskStatus[x.id]==="VERIFIED"),"Gate VERIFIED with unfinished tasks: "+id);
  }
  for(const row of accRows){
    check(row.length===4,"Acceptance row should have 4 columns: "+row[0]);
    const [id,status,evidence,note]=row;
    check(["NOT_RUN","PASS","FAIL","WAIVED"].includes(status),"Invalid acceptance status: "+id);
    if(["PASS","WAIVED"].includes(status)){
      check(evidenceOK(evidence),"PASS/WAIVED acceptance requires GitHub evidence: "+id);
      check(note&&note!=="-","PASS/WAIVED acceptance requires note: "+id);
    }
    if(status==="WAIVED")check(/ADR-\d{4}/.test(note||""),"WAIVED acceptance requires ADR ID in note: "+id);
    if(status==="FAIL")check(note&&note!=="-","FAIL acceptance requires issue note: "+id);
  }
  if(next==="NONE"){
    check(planTasks.every(x=>taskStatus[x.id]==="VERIFIED"),"Next task NONE while tasks unfinished");
  }else{
    const n=planTasks.find(x=>x.id===next);
    check(!!n,"Next task does not exist");
    if(n){
      check(n.gate===current,"Next task not in current gate");
      check(["TODO","IN_PROGRESS","BLOCKED"].includes(taskStatus[next]),"Next task already VERIFIED or missing");
    }
  }
  if(phase==="PLANNING_ONLY"){
    check(current==="G0"&&gateStatus.G0==="READY","Planning-only phase must be G0 READY");
    check(taskRows.every(row=>row[3]==="TODO"),"Planning-only phase cannot have started tasks");
    check(accRows.every(row=>row[1]==="NOT_RUN"),"Planning-only phase cannot claim acceptance tests");
  }
  for(const file of requiredFiles)check(file.exists,"Missing governance file: "+file.path);
  for(const link of ["MASTER_PLAN.md","PROGRESS.md","AGENTS.md","docs/WORK_LOG.md"])check(readme.includes(link),"README missing link: "+link);
  return {errors,summary:{gates:planGates.length,tasks:planTasks.length,acceptance:acceptanceIds.length,phase,current,next,version}};
};

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const read = (path) => readFileSync(resolve(root, path), "utf8");
const requiredPaths = [
  "MASTER_PLAN.md",
  "PROGRESS.md",
  "AGENTS.md",
  "docs/WORK_LOG.md",
  "docs/ADR_TEMPLATE.md",
  ".github/pull_request_template.md",
  "scripts/verify_governance.mjs",
  ".github/workflows/governance.yml"
];
const requiredFiles = requiredPaths.map(path => ({path, exists: existsSync(resolve(root,path))}));
const result = validate(read("MASTER_PLAN.md"), read("PROGRESS.md"), read("README.md"), requiredFiles);
console.log("Code City governance:", JSON.stringify(result.summary));
if (result.errors.length) {
  for (const error of result.errors) console.error("FAIL:", error);
  process.exitCode = 1;
} else {
  console.log("PASS: task IDs, gate order, acceptance IDs, status/evidence rules and project docs are consistent.");
  console.log("NOTE: This is a structural check only. Tests, Windows smoke and linked evidence must still be reviewed.");
}
