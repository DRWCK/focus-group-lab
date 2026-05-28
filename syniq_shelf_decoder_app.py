#!/usr/bin/env python3
"""
SYN-IQ — Shelf Decoder (vocabulary within IEP categories)
=========================================================
Run like the other tools:   streamlit run syniq_shelf_decoder_app.py

THE mechanism test. Not "do they use different words" (the text decoder
already showed that) but: do they pull DIFFERENT WORDS FROM THE SAME SHELF?
Split each response's words by IEP category using the embedded V3 dictionary
(1,890 words), then decode the agent from the AFFECTIVE words alone, the
INTERPRETIVE words alone, the ACTIVE words alone -- leave-one-question-out.

If agent is recoverable from a single shelf's vocabulary, identity lives in
WHICH words fill the category -- exactly the thing aff_pct/int_pct/act_pct
average away. That is the cart-vs-aisle claim, proven at the word level.

CONTROL: also decodes from NON-dictionary words (everything not on any shelf).
If that separates too, identity is everywhere, not specifically in IEP choice.
"""
import io, re
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneGroupOut
from PIL import Image

_INT = set("ability absolute absolutely abstract abstraction accuracy accurate algorithm algorithmic allows although always ambiguity ambiguous analogous analogously analogy analysis analytical analyze annotate annotated answer appear appeared appears appraisal appraise appraised approach approaches approximate architecture argue argued argues arguing argument arguments assert asserted assertion assertions assess assessment assume assumed assumes assuming assumption assumptions axiom axiomatic basis because bias biased boundaries boundary but calculate calculation categorical categorically categories categorize category causal causally causation cause caused causes certain certainly certitude challenge challenges circumscribe claim claimed claims clarify clarity classical classification classify clear cogent cogently cognition cognitive coherence coherent coherently communication compare comparison complex complexity comprehend comprehension computation computational compute conceivable conceive conceived concept concepts conceptual conceptualize conceptually conclude conclusion conclusions confirm confirmation conjecture conjectured conscious consequence consequences consider consideration consistency consistent consistently construe construed context contradict contradiction contradictory contrast correlate correlated correlation could counterargument counterexample counterpoint criteria criterion data debatable debate debated deconstruct deconstructed deconstruction deduce deduction define defined definite definitely definition definitive definitively delineate delineated demarcate demarcated demonstrate demonstration derivation derive derived derives describe described describing description determination determine diagnose diagnosed diagnosis diagnostic differ difference differences different differentiate differs discern discerned discernible disprove disproven dissect dissected distinguish effect effects elaborate elaborated elaboration elucidate elucidated empirical empirically enumerate enumerated epistemic epistemological equate equation equivalence equivalent erroneous error errors essential essentially estimate estimated estimation evaluate evaluation evidence evidently exact exactly examination examine except exemplified exemplify exists experiment experimental explain explained explaining explains explanation explanations explicit explicitly exploration explore explored exploring express expressing expression extrapolate extrapolated extrapolation fact facts factual factually fallacious fallacy falsifiable falsified falsify find finding formal formalize formula formulate formulated formulation found framework frameworks function fundamental fundamentally generalization generalize grasp grasped guess hence heuristic heuristics hierarchy however hypothesis hypothesize idea ideas identity if illuminate illuminated illuminating implausible implication implications implied implies imply implying incompleteness inconsistency inconsistent indicate indicated indicates indicating indication indicative individual infer inference infinite information insight insightful insights instead insufficient intellectual intellectually interaction internal interpolate interpret interpretation interpretations interpreted interpreting invalid investigate investigated investigation judge judgement judgment justification justified justify know knowing knowledge knowledgeable known language languages leads level likelihood likely limitations limits linguistic literal literally logic logical logically maybe meaning meaningful meaningfully measure measurement mechanism mechanisms meta method methodical methodically methodology metrics model models moreover namely natural nature nearly necessarily necessary necessity never nonetheless notice noticed noticing notion notions objection objectively objectivity observation observations observe observed obvious obviously order ordered organization organize otherwise ought paradigm paradox paradoxical paradoxically pattern patterns perhaps perspective philosophical philosophically philosophy physical plausibility plausible possibly postulate postulated postulation potential pragmatic pragmatically precise precision predicate predicated predict predictable predicted prediction predictions premise premises presumably presume presumed presumption principle principles probably problem procedural procedure process processes processing proof propose proposed proposition prove proven purpose quantify quantitative queried query question questions rather rational rationale rationality rationally realize realized reason reasoned reasoning reasons rebut rebuttal recognition recognize reconsider reconsidered refer reference refers refine refined refinement reflecting reflection refutation refute refuted requirement requires response responses result resulting results rigor rigorous rigorously role rule rules schema scrutinize scrutinized scrutiny seem seemed seems semantic semantically sequence sequential should significance significant significantly simple simply simultaneously singular specific specifically specification specify standard standards state states step steps stipulate stipulated strategies strategy structural structure subject subjective subjectively subjectivity substantiate substantiated sufficient sufficiently suggests summarize summarized summary suppose supposed supposedly supposition sure surely syllogism syllogistic synthesis synthesize synthesized system systematic systematically systems tactic tactics taxonomy technique test tested testing theorem theoretical theoretically theorize theory thereby therefore thesis think thinking thought thoughts thus trivial trivially unambiguous underlying understand understanding understood unique universal unless unlikely valid validate validation validity value values variable variables verification verify versus warrant warranted whereas whereby whether why word words would".split())
_AFF = set("abandoned ache aching adore adoring affection affectionate afraid agonize agonizing agony alienated alienation alive aliveness alone amazed amazement amazing ambivalence ambivalent among anger angrily angry anguish anguished anxiety anxious appreciate appreciation appreciative ashamed astonished astonishment attend attending attention attentive aware awareness awe awed awesome beautiful become becoming being bereaved bereavement betrayal betrayed between bitter bitterly bitterness bleak bliss blissful blissfully bodily bond bonding calm calming calmly care cared cares caring centered centering cheerful cherish cherished cherishing closeness comfort comfortable comforting compassion compassionate compassionately concern concerned concerns conflicted confused confusing confusion console contain contained containing contempt content contented contentment conversation cope coping crestfallen curiosity curious deep deeper deeply dejected dejection delighted depressed depressing depression depth depths desire desired desires desolate desolation despair despairing desperate desperation detached detachment devastated devastating devastation devoted devotion disappointed disappointment discomfort dismay dismayed distress distressed distressing distrust distrustful doubt doubtful doubting dread dreaded dreadful dreading ease easily easy ecstasy ecstatic elated elation embarrassed embarrassment embodied embodiment embrace embraced embracing emerge emergence emergent emerging emotion emotional emotionally emotions empathetic empathize empathy encounter encountered encountering enjoy enjoyed enjoying enjoyment enraged essence euphoria euphoric excellent excited excitement exist existence existing expanded expansion expansive experience experienced experiences experiencing experiential exposed fascinated fascinating fascination fear fearful fears feel feeling feelings feels felt flow flowed flowing fluid fluidity forlorn fragile fragility frantic frantically frustrated frustration fulfilled fulfilling fulfillment furious fury gentle gently genuine genuinely glad gloom gloomy good grateful gratefully gratitude great grief grieve grieved grieving grounded grounding guilt guilty gut happily happiness happy hate hatred haunted heart heartache heartbreak heartbroken heartfelt hearts held helpless helplessness hesitant hesitate hesitating hesitation hold holding homesick hope hopeful hopeless hopelessness hoping hostile hostility human humanity humility hunch hurt hurting imagination imagine imagined imagining indifference indifferent inner insecure insecurity instinct instinctive instinctively interested interesting intimacy intimate intimately intrigue intrigued intriguing intuition intuitive intuitively irritable irritated irritation isolated isolation journey joy joyful joyous kind kindly kindness lament lamented lamenting laugh laughed laughing let letting life lived living loneliness lonely lonesome long longing lost love loved loving mad marvel marveled marvelous meet meeting melancholic melancholy merry met mind minds mirror miserable misery moment moments moody mourn mourned mourning mutual mutually nervous nervously nice numb numbness open opening openness optimism optimistic outrage outraged overjoyed overwhelm overwhelmed overwhelming overwhelmingly pain painful panic panicked passion passionate passionately peace peaceful people perceive perceived perception perceptions person personal personally pleasant pleased pleasure poignancy poignant poignantly presence present presently pretty pride profound profoundly proud quiet quietly raw reality reassurance reassure reassured reassuring regret regretful regretfully regretting rejected rejection relate related relating relax relaxed relaxing release released releasing remorse remorseful resent resentful resentment resonance resonant resonate resonating rest rested restful resting restless restlessness reveal revealed revealing sad sadly sadness safe safety scared scary searching secure security seeking self sensation sensations sense sensed senses sensing sentimental serene serenity settle settled settling shame share shared sharing shattered silence silent smile smiled smiling soft soften softly somatic soothed soothing sorrow sorrowful soul soulful souls space spacious spaciousness spirit spirits spiritual spiritually still stillness stirred stirring stress stressed stressful suffer suffered suffering surface surfaces surfacing surprise surprised surprising sympathetic sympathize sympathy tearful tears tender tenderness tense tension tentative tentatively terrified terror thankful thankfully thankfulness thrilled together togetherness torment tormented torn touched touching tranquil tranquility tremble trembling troubled troubling truly trust trusted trusting trustworthy turmoil unaware uncertain uncertainty uncomfortable unease uneasy unhappy universe unsettled unsettling unsure upset vast visceral viscerally vulnerability vulnerable warm warmly warmth wary weariness weary well wistful wonder wondered wonderful wondering wondrous world worried worry worrying wound wounded wrath yearn yearning zeal zealous".split())
_ACT = set("access accessed accessing accomplish accomplished accomplishes accomplishing accomplishment achieve achieved achievement achievements achieves achieving act acting action actions activate activated activates activating activation acts adapt adaptation adapted adapting adapts address addressed addresses addressing adjust adjusted adjusting adjustment adjusts advance advanced advancement advances advancing ahead aim aimed aiming aims allocate allocated allocation application applied applies apply applying arrange arranged arrangement arrangements ask asked asking assemble assembled assign assigned assignment attempt attempted attempting attempts authorize authorized began begin beginning begins begun best better bolster bolstered break breaking bring bringing broken brought budget build building builds built calibrate calibrated call called calling campaign canvass canvassed carried carry carrying catalogue catalogued centralize centralized change changed changes changing channel channeled chart check checked checking choice choices choose choosing chose chosen circumvent coach collaborate collaborated collaboration commission commit commitment committed compile compiled complete completed completes completing completion concluded concludes concluding configure configured connect connected connecting connection connections consolidate construct constructed constructing constructs continuation continue continued continues continuing control controlled controlling controls conversion convert converted converting converts coordinate coordinated coordination craft crafted crafting create created creates creating creation customize deadline decide decided deciding decision decisions delegate delegated delegation deliver delivered delivering delivers delivery deploy deployed deploying deployment deploys design designed designing designs develop developed developing development develops did direct directed directing dive diving do does doing done draft drafting edit editing effort efforts eliminate eliminated elimination employ employed employing employs enable enabled end ended ending ends enforce enforced enforcement engage engaged engagement engineer engineering enroll enrolled enrollment equip equipped establish established establishes establishing establishment execute executed executes executing execution expedite facilitate facilitated facilitation finalize finalized finish finished finishes finishing fix fixed fixes fixing focus focused focusing form formation formed forming forms forward fund funded funding gather gathered gathering generate generated generates generating generation give given gives giving go goal goals goes going gone grew grow growing growth handle handled handles handling help helped helping helps hire hired hiring implement implementation implemented implementing implements improve improved improvement improving increase increased increasing initiate initiated initiates initiating initiation inspect inspection install installation installed integrate integrated integration intervene intervention invest invested investment iterate iterated iteration labor labored laboring launch launched launches launching lead leader leadership leading learn learned learning led made maintain maintained maintenance make makes making manage managed management manager managing map mapped mapping migrate migrated migration mobilize mobilized modification modified modifies modify modifying monitor monitored monitoring move moved movement movements moves moving navigate navigated navigation negotiate negotiated negotiation objective objectives obtain obtained offer offered offering onward operate operated operates operating operation operations optimization optimize optimized orchestrate outline outlined outsource overhaul oversee participate participated participation perform performance performed performing performs permit pilot piloted pioneer pioneered pitch pitched plan planned planning plans power powerful powerfully practice practiced preparation prepare prepared priorities prioritize prioritized priority proceed proceeded proceeding proceeds produce produced produces producing production productive program programmed progress progressed progresses progressing progression promote promoted promotion provide provided provides providing pursue pursued pursuit push pushed pushes pushing ran reaching rebuild rebuilt recruit recruited recruitment redesign reduce reduced reduction reform reformed refurbish register registered regulate regulated regulation reinforce reinforced relocate relocated remedy removal remove removed renovate renovated repair repaired replace replaced replacement replicate replicated request requested rescue rescued resolution resolve resolved resolves resolving restoration restore restored restructure restructured retrieve retrieved revamp revise revised revision run running runs schedule scheduled select selected selection send sending sent serve served serving ship shipped simplified simplify solution solutions solve solved solves solving start started starting starts stepped stepping stop stopped stopping streamline streamlined strive strived striving strove struggle struggled struggles struggling submission submit submitted succeed succeeded succeeds success successful successfully supplied supply support supported supporting survey surveyed sustain sustainability sustained tackle tackled tackles tackling take taken takes taking target targets task tasked tasks taught teach teaching train trained training transform transformation transformed transforming transforms transition transitioned tried tries trigger triggered triggering triggers troubleshoot try trying turn turned turning upgrade upgraded use used uses using utilize utilized utilizes utilizing visit visited visiting volunteer volunteered went win winner winning won work worked working works write writes writing written wrote".split())
SHELVES = {"Interpretive": _INT, "Affective": _AFF, "Active": _ACT}
_ALL_IEP = _INT | _AFF | _ACT
_TOK = re.compile(r"[a-z]+")

def _bag(text, keep, invert=False):
    toks = _TOK.findall(str(text).lower())
    if invert:
        return " ".join(t for t in toks if t not in keep)
    return " ".join(t for t in toks if t in keep)

def _loqo_acc(texts, y_agent, y_q, min_df=3):
    if all(not t.strip() for t in texts):
        return np.nan
    try:
        vec = TfidfVectorizer(min_df=min_df, sublinear_tf=True)
        X = vec.fit_transform(texts)
    except ValueError:
        return np.nan
    if X.shape[1] == 0:
        return np.nan
    logo = LeaveOneGroupOut(); accs = []
    for tr, te in logo.split(X, y_agent, groups=y_q):
        if len(np.unique(y_agent[tr])) < 2:
            continue
        m = LogisticRegression(max_iter=3000).fit(X[tr], y_agent[tr])
        accs.append(m.score(X[te], y_agent[te]))
    return float(np.mean(accs)) if accs else np.nan

def shelf_decode(full, min_df=3):
    texts = full["response_text"].astype(str).tolist()
    y_agent = np.asarray(full["agent_label"].astype(str).to_numpy(), dtype=object)
    y_q     = np.asarray(full["question_id"].astype(str).to_numpy(), dtype=object)
    chance = 1 / len(np.unique(y_agent))
    rows = []
    for name, shelf in SHELVES.items():
        rows.append((name, _loqo_acc([_bag(t, shelf) for t in texts], y_agent, y_q, min_df)))
    rows.append(("All IEP words", _loqo_acc([_bag(t, _ALL_IEP) for t in texts], y_agent, y_q, min_df)))
    rows.append(("Non-IEP (control)", _loqo_acc([_bag(t, _ALL_IEP, invert=True) for t in texts], y_agent, y_q, min_df)))
    return pd.DataFrame(rows, columns=["word_shelf", "agent_loqo"]), chance

def shelf_wardrobe(full, shelf):
    texts = [_bag(t, shelf) for t in full["response_text"].astype(str)]
    y = np.asarray(full["agent_label"].astype(str).to_numpy(), dtype=object)
    try:
        vec = TfidfVectorizer(min_df=3, sublinear_tf=True); X = vec.fit_transform(texts)
    except ValueError:
        return {}
    if X.shape[1] == 0: return {}
    m = LogisticRegression(max_iter=3000).fit(X, y)
    vocab = np.array(vec.get_feature_names_out())
    coef = m.coef_ if m.coef_.shape[0] > 1 else np.vstack([-m.coef_[0], m.coef_[0]])
    return {str(c): vocab[np.argsort(coef[i])[::-1][:10]].tolist() for i, c in enumerate(m.classes_)}

def figure(df, chance):
    fig, ax = plt.subplots(figsize=(7.087, 3.6))
    vals = (df["agent_loqo"].fillna(0) * 100).tolist()
    colors = ["#984ea3","#e41a1c","#4daf4a","#377eb8","#999999"][:len(df)]
    ax.bar(df["word_shelf"], vals, color=colors)
    ax.axhline(chance*100, ls=":", color="k", lw=1, label="chance " + format(chance,".0%"))
    for i,v in enumerate(vals): ax.text(i, v+1.5, format(v,".0f")+"%", ha="center", fontsize=9, fontweight="bold")
    ax.set_ylim(0,105); ax.set_ylabel("agent recoverability % (leave-1-Q-out)", fontsize=9)
    ax.set_title("Is the agent in the words ON each shelf?", fontsize=10, fontweight="bold")
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df["word_shelf"], rotation=15, ha="right", fontsize=8)
    ax.legend(fontsize=8); fig.tight_layout(); return fig

def tiff_bytes(fig, dpi=600):
    buf=io.BytesIO(); fig.savefig(buf,format="tiff",dpi=dpi,bbox_inches="tight",pil_kwargs={"compression":"tiff_lzw"})
    buf.seek(0); im=Image.open(buf)
    if im.mode in ("RGBA","LA","P"):
        im=im.convert("RGBA"); bg=Image.new("RGB",im.size,"white"); bg.paste(im,mask=im.split()[-1]); im=bg
    out=io.BytesIO(); im.save(out,format="tiff",compression="tiff_lzw"); out.seek(0); return out.getvalue()

def check_password():
    exp=st.secrets.get("app_password",None)
    if not exp: st.error("No password set. Add app_password in Secrets."); st.stop()
    if st.session_state.get("auth_ok"): return
    st.title("SYN-IQ -- Authorized Access")
    pw=st.text_input("Password",type="password")
    if pw and pw==exp: st.session_state["auth_ok"]=True; st.rerun()
    elif pw: st.error("Incorrect password.")
    st.stop()

def main():
    st.set_page_config(page_title="SYN-IQ Shelf Decoder", layout="wide")
    check_password()
    st.title("SYN-IQ -- Shelf Decoder")
    st.caption("Do the models pull different words from the SAME IEP shelf? "
               "Embedded V3 dictionary, leave-one-question-out.")
    with st.sidebar:
        files=st.file_uploader("Agent CSV(s)",type=["csv"],accept_multiple_files=True)
        temp=st.text_input("Temperature (lock to ONE)",value="NATIVE")
        allow_mix=st.checkbox("Allow mixed temperatures",value=False)
        min_df=st.slider("min_df",2,10,3)
    if not files:
        st.info("Upload agent CSV(s) with response_text. Lock to NATIVE."); return
    fr=[]
    for f in files:
        d=pd.read_csv(f)
        if "agent" in d: d["agent"]=d["agent"].replace({"Sophia":"ChatGPT","sophia":"ChatGPT"}); d["agent_label"]=d["agent"]
        fr.append(d)
    full=pd.concat(fr,ignore_index=True)
    if "response_text" not in full: st.error("No response_text column."); return
    if temp.strip() and "temperature" in full: full=full[full["temperature"]==temp.strip()].copy()
    temps=sorted(full["temperature"].unique()) if "temperature" in full else []
    if len(temps)>1 and not allow_mix:
        st.error("Multiple temperatures present. Lock to one or override."); st.stop()
    nag=full["agent_label"].nunique() if "agent_label" in full else 0
    st.write("Loaded " + str(len(full)) + " responses, " + str(nag) + " agents, "
             + str(full["question_id"].nunique()) + " questions")
    if nag<2: st.warning("Need >=2 agents -- upload all agent files together."); return
    if not st.button("Decode by shelf",type="primary"): return
    with st.spinner("Splitting words by shelf and decoding..."):
        df,chance=shelf_decode(full,min_df)
    st.subheader("Agent recoverable from each shelf's vocabulary (leave-1-Q-out)")
    show=df.copy(); show["agent_loqo"]=(show["agent_loqo"]*100).round(1); show["chance_pct"]=round(chance*100,1)
    st.dataframe(show,use_container_width=True)
    ctrl=df[df.word_shelf=="Non-IEP (control)"]["agent_loqo"].iloc[0]
    shelves_above=int((df[df.word_shelf.isin(SHELVES)]["agent_loqo"]>chance+0.05).sum())
    if shelves_above>=1:
        st.success("Agent is recoverable from within-shelf word choice (" + str(shelves_above)
                   + "/3 shelves beat chance). Identity lives in WHICH words fill the category -- "
                   "the thing the percentages average away.")
    else:
        st.info("No shelf beats chance much -- within-category word choice may not carry the agent here.")
    if not np.isnan(ctrl):
        st.caption("Control: non-dictionary words decode agent at " + format(ctrl,".0%")
                   + " (chance " + format(chance,".0%") + "). If as high as the shelves, identity is not specific to IEP vocabulary.")
    st.subheader("Wardrobe by shelf -- distinctive words per agent")
    for name, shelf in SHELVES.items():
        w=shelf_wardrobe(full,shelf)
        if w:
            st.markdown("**" + name + " shelf**")
            st.dataframe(pd.DataFrame(dict([(a,(ws+['']*10)[:10]) for a,ws in w.items()])),use_container_width=True)
    fig=figure(df,chance); st.pyplot(fig)
    st.download_button("Download figure TIFF (600 dpi)",tiff_bytes(fig),file_name="fig_shelf_decode.tiff",mime="image/tiff")
    st.download_button("Download table CSV",df.to_csv(index=False),file_name="fig_shelf_decode.csv",mime="text/csv")

if __name__=="__main__":
    main()
