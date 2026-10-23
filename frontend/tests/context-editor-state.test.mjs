import {test} from "node:test";
import assert from "node:assert/strict";
import {blankReview,internalDestination} from "../src/features/contexts/context-editor-state.ts";

test("reopened review has no carried rationale or attestations",()=>{
 const old=blankReview(); old.rationale="Conferência da versão anterior";
 old.references_checked=old.scopes_checked=old.alternatives_checked=old.limitations_checked=true;
 const current=blankReview();
 assert.equal(current.rationale,"");
 for(const key of ["references_checked","scopes_checked","alternatives_checked","limitations_checked"])assert.equal(current[key],false);
 assert.equal(old.rationale,"Conferência da versão anterior");
 assert.notEqual(old,current);
 assert.equal("expected_revision" in current,false);
});

test("unsaved SPA navigation includes parent navigation and another editor revision",()=>{
 const here="http://127.0.0.1:3000/painel/contextos/id#evidence";
 assert.equal(internalDestination("/painel",here),"/painel");
 assert.equal(internalDestination("/painel/contextos/outro",here),"/painel/contextos/outro");
 assert.equal(internalDestination("?indicador=desocupacao",here),"/painel/contextos/id?indicador=desocupacao");
});

test("same-page references, new tabs, external sites and invalid URLs retain editor",()=>{
 const here="http://127.0.0.1:3000/painel/contextos/id";
 assert.equal(internalDestination("#source-id",here),null);
 assert.equal(internalDestination("/painel/fontes",here,"_blank"),null);
 assert.equal(internalDestination("https://ibge.gov.br/",here),null);
 assert.equal(internalDestination("javascript:alert(1)",here),null);
 assert.equal(internalDestination("http://[",here),null);
 assert.equal(internalDestination("http://user@127.0.0.1:3000/painel",here),null);
});
