import test from "node:test";
import assert from "node:assert/strict";
import { ideaScreen, ideaDevelopmentPath, updateQuickIdea, guidedEntryQuestion } from "../src/features/ideas/navigation.ts";
import { emptyIdea } from "../src/features/ideas/state.ts";

test("opening an existing idea stays simple unless preparation is explicitly requested", () => {
  assert.equal(ideaScreen({}),"quick");
  assert.equal(ideaScreen({desenvolver:"unknown"}),"quick");
  assert.equal(ideaScreen({desenvolver:["proposta"]}),"quick");
  assert.equal(ideaScreen({desenvolver:"proposta"}),"choice");
  assert.equal(ideaScreen({modo:"guiado"}),"guided");
  assert.equal(ideaScreen({modo:"manual"}),"manual");
});

test("preparation links preserve the saved identity and explicit choice of mode", () => {
  assert.equal(ideaDevelopmentPath("saved-id"),"/painel/ideias/saved-id?desenvolver=proposta");
  assert.equal(ideaScreen(Object.fromEntries(new URLSearchParams(ideaDevelopmentPath("saved-id","guided").split("?")[1]))),"guided");
  assert.match(ideaDevelopmentPath("id/with space","manual"), /^\/painel\/ideias\/id%2Fwith%20space\?/);
});

test("quick title and summary edits preserve advanced content, figures and assisted provenance", () => {
  const input=emptyIdea();
  input.content.problem="Original problem";
  input.content.proposal="Confirmed measure";
  input.content.impacts=[{year:2026,amount:"1000000000000.01",description:"Existing estimate",impact_type:"NEW_EXPENSE"}];
  input.content.sources=[{source_id:"source-1",usage_description:"Existing explanation"}];
  input.beneficiaries="Confirmed group";
  input.risks="Existing risk";
  input.assisted_fields=["problem"];
  const next=updateQuickIdea(input,"  Updated title  ","  Short idea  ");
  assert.equal(next.title,"Updated title");
  assert.equal(next.content.title,next.title);
  assert.equal(next.summary,"Short idea");
  assert.equal(next.content.summary,next.summary);
  assert.deepEqual(next.content.impacts,input.content.impacts);
  assert.deepEqual(next.content.sources,input.content.sources);
  assert.equal(next.content.problem,"Original problem");
  assert.equal(next.content.proposal,"Confirmed measure");
  assert.equal(next.beneficiaries,input.beneficiaries);
  assert.equal(next.risks,input.risks);
  assert.deepEqual(next.assisted_fields,input.assisted_fields);
  assert.equal(input.title,"");
});


test("first guided entry skips the saved title and phrase but keeps deliberate earlier-question navigation", () => {
  const start={current:0,started:false,saved:true,title:"Saved title",summary:"Saved phrase"};
  assert.equal(guidedEntryQuestion(start),2);
  assert.equal(guidedEntryQuestion({...start,started:true}),0);
  assert.equal(guidedEntryQuestion({...start,current:1}),1);
  assert.equal(guidedEntryQuestion({...start,current:5,started:true}),5);
  assert.equal(guidedEntryQuestion({...start,saved:false}),0);
  assert.equal(guidedEntryQuestion({...start,title:" "}),0);
  assert.equal(guidedEntryQuestion({...start,summary:" "}),0);
});
