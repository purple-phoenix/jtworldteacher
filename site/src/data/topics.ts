// Topic hubs: a hand-curated map of recurring topics to the episodes that
// cover them. This is the single source of truth for /topics/ and the
// "Topics" row on episode pages; episode .md files are not touched.
//
// Mention timestamps are whole seconds, taken from cue starts in the episode's
// transcript (catalog/spaces/transcripts/<audio-slug>.vtt), which is aligned to
// the published, edited audio. Each links to /podcast/<slug>/#t=<seconds>.
//
// Notes and intros attribute views to JT and guests; don't state them as fact.
// The topic pages fail the build if a slug isn't a published episode or a
// timestamp runs past the episode's durationSeconds.

export interface TopicMention {
  /** Seconds from the start of the published audio. */
  t: number;
  note: string;
}

export interface TopicEpisode {
  /** Episode id: the filename in src/content/episodes/ without `.md`. */
  slug: string;
  mentions: TopicMention[];
}

export interface Topic {
  id: string;
  name: string;
  /** One line for the /topics/ index. */
  summary: string;
  /** Meta description for the topic page. */
  description: string;
  intro: string[];
  related: string[];
  episodes: TopicEpisode[];
}

export const TOPICS: Topic[] = [
  {
    id: "archons",
    name: "The Archons",
    summary: "The Against the Archons thread: Gnostic rulers, planetary toll houses, and the overlay JT says they run.",
    description: "Episodes where JT McCarthy and guests discuss the Archons: Gnostic rulers, aerial toll houses, the seven planetary spheres and Against the Archons.",
    intro: [
      "The Archons are the spine of JT's Against the Archons series. He draws on Gnostic texts like the Apocryphon of John, the Orthodox teaching of the aerial toll houses, and the seven planetary spheres of late-antique cosmology. From these he reads the archons as rulers who, in his telling, captured humanity inside a reality overlay and installed its vices.",
      "Across these episodes he maps the seven classical planets onto seven “archonic” behavior patterns. He argues that awareness of them is not the same as awakening, and he sets the ancient accounts beside remote-viewing session data from Intuitive Underground. Guests and callers push back about as often as they agree. These are JT's interpretations of religious and esoteric sources, offered as inquiry, not settled fact.",
    ],
    related: ["simulation", "the-hierarchy", "psychic-gene", "technical-remote-viewing"],
    episodes: [
      {
        slug: "2025-05-28-bigfoot-state-of-reality-morgan-dan",
        mentions: [
          { t: 2692, note: "The viewers attribute human engineering to non-human intelligences, and Dan Mann says terms like demiurge, archons or Anunnaki all get used." },
          { t: 8031, note: "JT argues the New Testament's 'principalities and rulers of the air' are the archons, linking abductee accounts and government disclosures to them." },
        ],
      },
      {
        slug: "2025-07-16-human-nature-and-the-paranormal",
        mentions: [
          { t: 987, note: "JT states the claim that humans are here involuntarily, something done to us by the beings history calls the Archons." },
          { t: 6297, note: "JT argues, citing The Cosmic Serpent, that DNA is the demiurge and archons are a subset of the overlay built on it." },
          { t: 6926, note: "JT says archons keep people from realizing they are in an overlay so they will not prepare for death." },
          { t: 9982, note: "JT describes his semi-Gnostic Christian stance: planets represent the archons, which he links to 'princes of the air' and aerial toll houses." },
        ],
      },
      {
        slug: "2026-01-11-karmic-deep-impact",
        mentions: [
          { t: 7246, note: "JT says conscious awareness of the archons is returning and being debated, and imagines Bailey foresaw non-human intelligence openly ruling." },
          { t: 8282, note: "JT cautions against chaos magic and making deals with the archons, arguing a bargain with your captor makes you a willing participant." },
        ],
      },
      {
        slug: "2026-01-20-thunderdome-saturn-neptune-and-the-archons",
        mentions: [
          { t: 3659, note: "JT walks through the ancient model: aerial toll houses, ascent through seven planetary spheres, and archons who must let a soul pass." },
          { t: 3896, note: "JT says the archons built an artificial eighth sphere, a matrix, a motif found in esoteric Buddhism and later Theosophy." },
          { t: 5042, note: "JT maps the seven planets onto archonic behavior patterns that must be addressed while alive, linking them to karma." },
        ],
      },
      {
        slug: "2026-01-27-the-empire-never-ended-secret-of-the-psychic-gene",
        mentions: [
          { t: 1553, note: "JT retells the Gnostic creation story of Sophia and the Demiurge, and argues the Demiurge can be read as DNA." },
        ],
      },
      {
        slug: "2026-03-27-you-re-screwed-astrology-questions-answered",
        mentions: [
          { t: 8447, note: "JT says some remote viewers report people from outside the overlay, possibly fallen angels, and plans a space called 200 Griefers." },
          { t: 9404, note: "JT relays remote viewer claims that archons, or griefers, can live a human life in an hour, framing it as only reporting." },
        ],
      },
      {
        slug: "2026-04-01-the-return-of-the-king",
        mentions: [
          { t: 3260, note: "JT answers listeners who ask how to escape the archons and reality overlay: shed vices and resentment, and pursue renunciation." },
        ],
      },
      {
        slug: "2026-04-02-the-against-the-archons-emergent-archetype-in-media",
        mentions: [
          { t: 874, note: "JT explains how the Against the Archons name came about and why Dungeon Crawler Carl fits the theme." },
          { t: 965, note: "JT discusses an evangelical author who accuses him of demonic deception and notes Gnosticism began as an insult for early Christian groups." },
          { t: 2319, note: "JT argues organized resistance to the archons is an emerging archetype surfacing from the collective unconscious, with art leaking it first." },
        ],
      },
      {
        slug: "2026-04-25-technical-remote-viewing",
        mentions: [
          { t: 21665, note: "JT recalls earlier spaces on being stuck in the reality overlay by the archons and escape through moksha." },
          { t: 22061, note: "JT says ancient sources hold that archons built the overlay and instilled greed and hatred to harvest suffering." },
          { t: 22988, note: "A guest says he does not believe archons or demons can remove anyone from the universe, offering a more comforting view." },
        ],
      },
      {
        slug: "2026-04-29-oriental-archons",
        mentions: [
          { t: 1767, note: "JT argues archons were both planets and their embodying beings, later displaced by demonology, toll houses and the seven deadly sins." },
          { t: 4622, note: "JT links the Devas and Asuras of the Pontic steppe, flipped between India and Iran, to the archons and the word devil." },
          { t: 5461, note: "JT describes the archon story as beginning with a global war between rival Anunnaki, recorded in Mesopotamian texts and the Harappan ruins." },
        ],
      },
      {
        slug: "2026-05-02-final-feedback-intuitive-underground-were-right-about-everything",
        mentions: [
          { t: 2776, note: "JT calls the Intuitive Underground reports a Rosetta Stone for decoding Gnostic and esoteric texts, citing the Apocryphon of John." },
          { t: 4185, note: "JT describes Gnostic movements being crushed and their books burned, arguing surviving texts therefore use coded language." },
          { t: 6800, note: "JT previews an Against the Archons space on the Watchers and Nephilim theory, tying fallen angels to the simulation idea." },
        ],
      },
      {
        slug: "2026-05-08-disclosure-and-technical-remote-viewing",
        mentions: [
          { t: 11006, note: "JT says archons, the 'space dicks', appear in myth as gods, and notes channeled groups claiming similar identities, which he avoids." },
          { t: 11507, note: "JT links remote viewing to Rudolf Steiner's idea of clairvoyance building the 'eighth sphere', which he equates with the simulation." },
        ],
      },
      {
        slug: "2026-07-04-the-revelation-of-the-hierarchy",
        mentions: [
          { t: 671, note: "JT says the revelation involves the return of beings once called gods, which he calls archons, into human awareness." },
          { t: 1492, note: "JT explains archons as rulers, planets and the Gnostic beings who he says hijacked humanity into a simulation and installed our vices." },
          { t: 5018, note: "JT reads the archaic revival, from Crowley to the Council of Nine channeling, as the archons returning to collective consciousness." },
        ],
      },
      {
        slug: "2026-07-05-american-disclosure",
        mentions: [
          { t: 3467, note: "JT argues the simulation's creators were extraterrestrial, which history knows as the archons, called gods by pagans." },
        ],
      },
      {
        slug: "2026-09-16-the-world-tree-and-the-eclipse-in-leo",
        mentions: [
          { t: 2803, note: "JT says a recent Rick and Morty episode inserted the archon story of a false, farmed reality into the world-tree metaphor." },
          { t: 2960, note: "JT discusses the simulation's apparent injustice, citing the Apocryphon of John and the IU canon on humans as prisoners." },
          { t: 3818, note: "JT casts the tree as the demiurge, the simulation's internal ruler, and argues via The Cosmic Serpent that DNA is the demiurge." },
        ],
      },
    ],
  },
  {
    id: "technical-remote-viewing",
    name: "Technical Remote Viewing",
    summary: "Ed Dames' TRV lineage, Intuitive Underground's sessions, and what the protocol can and can't claim.",
    description: "Episodes on Technical Remote Viewing (TRV): Ed Dames' protocol, Morgan Farrell and Intuitive Underground, the Kill Shot and hit rates, with timestamps.",
    intro: [
      "Technical Remote Viewing (TRV) is the structured, blind-tasked protocol Ed Dames developed out of the US military's controlled remote viewing work. It's the method JT trusts most. It's also the one his most frequent guest teaches: Morgan Farrell, an instructor with Intuitive Underground.",
      "On the show, Morgan explains tasking, target reference numbers, feedback and how sessions get graded. JT and his guests go through Intuitive Underground's projects, from election calls to the “Kill Shot” solar-event target, and argue about other viewing groups. Remote viewing is contested. The hits claimed here are the speakers' own accounts, not independently verified results.",
    ],
    related: ["astro-rv", "simulation", "disclosure", "archons"],
    episodes: [
      {
        slug: "2025-05-28-bigfoot-state-of-reality-morgan-dan",
        mentions: [
          { t: 781, note: "Dan Mann describes entering remote viewing in 2012 via Ed Dames on Coast to Coast; Morgan Farrell then describes his training." },
          { t: 1935, note: "JT frames Intuitive Underground's sessions as a Rosetta Stone for decoding 2,000 years of clairvoyant data hidden in allegory." },
          { t: 7342, note: "A caller asks how to trust the data and whether viewers tap collective consciousness; the guests defend the Ed Dames-school method." },
          { t: 16301, note: "A guest explains remote viewing as a data-collection system whose structure and protocol maximize signal-to-noise, ranking it above general psychic methods." },
        ],
      },
      {
        slug: "2025-05-31-astro-rv-project-morgan-farrell",
        mentions: [
          { t: 984, note: "Morgan Farrell traces CRV from Puthoff, Swann and Targ to Ed Dames' TRV, a reorganized protocol built for faster operational viewing." },
          { t: 2102, note: "Morgan describes TRV's targeting discipline: strip out the tasker's intent, and remember the matrix reads wording literally." },
          { t: 13253, note: "Morgan Farrell describes Intuitive Underground sessions suggesting a hypersonic, EMP-like West Coast event, and links wider data to Dames' kill shot." },
        ],
      },
      {
        slug: "2025-06-27-thinking-about-world-war-3",
        mentions: [
          { t: 4598, note: "Morgan Farrell reads Intuitive Underground's 2022 deep-mind probe of Putin, describing a leader prepared to use nuclear weapons as a last resort." },
          { t: 5943, note: "Morgan Farrell describes Intuitive Underground's repeated U.S.-China trajectory sessions, which keep returning a downward-spiral archetype with kinetic activity." },
          { t: 8784, note: "JT discusses Courtney Brown and Farsight, saying he does not call Brown a grifter and trusts the viewers more than the reporting." },
        ],
      },
      {
        slug: "2025-07-16-human-nature-and-the-paranormal",
        mentions: [
          { t: 423, note: "JT introduces Morgan Farrell and Intuitive Underground's decade-plus Canon project mapping the nature of reality, including paranormal themes." },
          { t: 9398, note: "JT cites Ed Dames and the 'kill shot' as remote-viewing lore that global war precedes a solar event or pole shift." },
          { t: 12690, note: "JT says he cross-checks public viewer data, citing an Intuitive Underground target where a supposed Dyson sphere showed a ship." },
        ],
      },
      {
        slug: "2026-01-11-karmic-deep-impact",
        mentions: [
          { t: 1642, note: "JT says remote viewing is one of his three interests, explaining the former government psychic programs and private consulting groups that followed." },
        ],
      },
      {
        slug: "2026-01-20-thunderdome-saturn-neptune-and-the-archons",
        mentions: [
          { t: 2104, note: "JT cites Intuitive Underground sessions forecasting a three-stage crisis: an April urban blackout, a July political transition, and autumn coastal flooding." },
          { t: 3611, note: "JT discusses Intuitive Underground data on the tunnel of light as a trap and a corrupt post-death tribunal, matching ancient sources." },
          { t: 4228, note: "JT argues remote viewers and astrologers are awareness specialists who mistake awareness for the answer to the afterlife problem." },
        ],
      },
      {
        slug: "2026-01-27-the-empire-never-ended-secret-of-the-psychic-gene",
        mentions: [
          { t: 3899, note: "JT says remote viewers in simulation sessions have surfaced the word Terra, and that he refuses to let RV replace Christian theology." },
          { t: 4275, note: "JT recalls Morgan's remote-viewing account of base reality, a war, experiments on prisoners and a cathedral-like building, and voices skepticism." },
        ],
      },
      {
        slug: "2026-03-19-the-long-emergency",
        mentions: [
          { t: 3432, note: "JT recalls Intuitive Underground session data predicting China would achieve, or appear to achieve, technological parity with the US." },
          { t: 5906, note: "JT describes the Future Forecasting Group's 'luminosity event' sessions: an East Coast blackout in April, then a political transition in July." },
          { t: 6506, note: "JT discusses what remote viewers withhold, his years working with Morgan Farrell, and his pressure on them to publish session data." },
          { t: 6786, note: "JT says remote viewers since the 1990s have predicted a 'kill shot' solar event, tied to war and a possible pole shift." },
        ],
      },
      {
        slug: "2026-03-27-you-re-screwed-astrology-questions-answered",
        mentions: [
          { t: 4720, note: "JT cites Intuitive Underground remote viewing data on China overtaking the US as support for his forecast." },
          { t: 8950, note: "JT discusses remote viewer sessions on the Kill Shot, pole shifts and a Doom Room scenario, framed as a thought exercise." },
        ],
      },
      {
        slug: "2026-04-01-the-return-of-the-king",
        mentions: [
          { t: 4779, note: "JT critiques the public remote-viewing groups and ranks viewers by reliability and experience." },
          { t: 5070, note: "JT says Morgan and Dan's session material saw a tower on the West Coast, and notes viewers rarely compare each other's data." },
        ],
      },
      {
        slug: "2026-04-02-the-against-the-archons-emergent-archetype-in-media",
        mentions: [
          { t: 2939, note: "JT recounts a remote viewer's career reading that pictured him inside a machine, which led him to Intuitive Underground and Morgan." },
        ],
      },
      {
        slug: "2026-04-05-astro-rv-alert",
        mentions: [
          { t: 1247, note: "JT recalls an Intuitive Underground session of a West Coast tower attack with protesters, and compares it to the WAR data." },
          { t: 1437, note: "JT reads the second viewer's imagery, suggesting analytical overlay explains the Independence Day-like scene and the glowing DNA may mean radioactive fallout." },
          { t: 2903, note: "JT argues Astro-RV projects should use the methodology he and Morgan developed rather than the WAR team's approach." },
        ],
      },
      {
        slug: "2026-04-22-suck-it-dan-waites",
        mentions: [
          { t: 4584, note: "JT recounts a guest's claim that Lyn Buchanan's CRV timelines predict event timing, and objects that viewers vary by about five years." },
          { t: 6792, note: "Morgan Farrell says Ed Dames knew he wasn't the best viewer but led remote viewing's expansion and refinement beyond its military roots." },
          { t: 7397, note: "JT defends technical remote viewing and says the TRV community is needed now, with Ed Dames gone." },
        ],
      },
      {
        slug: "2026-04-25-technical-remote-viewing",
        mentions: [
          { t: 402, note: "JT says a talk about AI made him link prompt and context engineering to Ed Dames's TRV and the reality overlay." },
          { t: 10040, note: "A debate over whether TRV should be the one tool, with JT defending a focused method and a guest urging multiple modalities." },
          { t: 18764, note: "JT lays out his role: promoting Dames's TRV legacy and training, and pairing it with astrology to scale remote viewing." },
          { t: 19084, note: "JT describes hiring a technical remote viewer for Dames-style Kill Shot work, such as finding safer places to be in a crisis." },
        ],
      },
      {
        slug: "2026-04-29-oriental-archons",
        mentions: [
          { t: 4233, note: "JT says remote viewers looking at the moon tend to report pale Nordic-looking beings, and relates this to Asian moon-people legends." },
          { t: 4864, note: "JT recounts Morgan Farrell's session data on the overlay's origin: a global war with three parties, stocky experimenters, and a gray ambassador." },
          { t: 5062, note: "JT cites other remote-viewing groups, not Morgan's, reporting subterranean gateways and contact with biological immortals in caves." },
        ],
      },
      {
        slug: "2026-05-02-final-feedback-intuitive-underground-were-right-about-everything",
        mentions: [
          { t: 1636, note: "JT walks through the Intuitive Underground team's forecasts and reports, scoring each against later events and defending their track record." },
          { t: 4441, note: "JT argues Intuitive Underground alone refused to sweep its data under the rug and is denied credit by other remote viewers." },
          { t: 5222, note: "JT claims no other remote-viewing group matches Intuitive Underground's level of verification and feedback, contrasting it with Future Forecasting." },
        ],
      },
      {
        slug: "2026-05-07-ufox-the-crusade-within-ufology",
        mentions: [
          { t: 2598, note: "JT pushes back on guilt by association linking remote viewing to Epstein emails and Scientology, calling that bad logic." },
          { t: 3658, note: "A speaker explains the U.S. remote viewing program as a reaction to a Soviet paranormal program, and why a private industry exists." },
        ],
      },
      {
        slug: "2026-05-08-disclosure-and-technical-remote-viewing",
        mentions: [
          { t: 3264, note: "Morgan Farrell presents a blind-targeted Intuitive Underground side session on the released UAP video; viewers described man-made, military technology." },
          { t: 4529, note: "JT outlines catastrophe forecasts from remote viewers, including pole shift or micro nova, called the kill shot in technical remote viewing." },
          { t: 8424, note: "JT introduces Morgan as one of Ed Dames' protégés, who trained with Dames, before Morgan answers on moon and Mars viewing." },
        ],
      },
      {
        slug: "2026-09-02-technical-remote-viewing-and-the-kill-shot",
        mentions: [
          { t: 880, note: "Morgan Farrell explains remote viewing as both protocol and method, describing tasker, blind viewer, target reference numbers and feedback." },
          { t: 1383, note: "Morgan describes how Ed Dames refined controlled remote viewing into TRV, a staged, rapid-fire prompt-and-response method." },
          { t: 3400, note: "Morgan recounts the Kill Shot, an Earth-facing X-class solar flare seen by Dames' viewers, citing the 1859 Carrington event." },
        ],
      },
      {
        slug: "2026-09-09-intuitive-underground-and-the-power-of-remote-viewing",
        mentions: [
          { t: 73, note: "Morgan Farrell describes his week-three training exercise of working front-loaded to remote view the next morning's front-page photo, and its hit." },
          { t: 854, note: "Morgan Farrell recounts Intuitive Underground's 2016 election project, where blind viewers' sessions each called Trump and he named him in session." },
          { t: 1701, note: "Asked about his mission, Morgan Farrell says Intuitive Underground began as a study group and aims to demonstrate remote viewing's power." },
          { t: 3062, note: "Matt asks about tracking hit rates, and Morgan explains perception-by-perception grading and the Targ scale; JT cites socialrv's roughly 51%." },
          { t: 4116, note: "Morgan Farrell describes the experimental target, 'the most significant remote viewing target', that led the group to the nature of reality." },
        ],
      },
      {
        slug: "2026-09-16-the-world-tree-and-the-eclipse-in-leo",
        mentions: [
          { t: 4706, note: "JT discusses how remote viewers need ways to fund their work and voices his criticism of groups that sell crypto forecasts." },
        ],
      },
    ],
  },
  {
    id: "astro-rv",
    name: "Astro-RV",
    summary: "Astrology as a timing layer for blind remote viewing: the project JT and Morgan Farrell built, and its imitators.",
    description: "Episodes on Astro-RV, JT McCarthy's method of pairing astrological timing with blind remote viewing, with timestamped mentions of the experiments and critiques.",
    intro: [
      "Astro-RV is JT's name for pairing his two disciplines. As he describes it, astrology supplies the time coordinates (a transit, an ingress, an eclipse) and blind remote viewing supplies the detail of what happens then. He argues the combination could push viewing past its usual six-to-eighteen-month horizon.",
      "JT developed the approach with Morgan Farrell. These episodes cover their first experiments and JT's critiques of later Astro-RV sessions by other teams, including Dan Waites' World Astrology Report. They also include the 2026 “alert” episodes, where JT put the method to work in real time. Results and hits are as JT and his guests describe them.",
    ],
    related: ["technical-remote-viewing", "saturn-neptune", "mundane-astrology", "eclipses"],
    episodes: [
      {
        slug: "2025-05-31-astro-rv-project-morgan-farrell",
        mentions: [
          { t: 3940, note: "JT and Morgan explain Astro RV: astrology supplies timing, remote viewing supplies event detail, extending viewing past roughly 6 to 18 months." },
          { t: 4848, note: "JT describes the first joint Astro RV experiment, anchored on the nuclear-age chart, and presents the Iran-Israel weekend de-escalation as a hit." },
          { t: 9668, note: "Morgan Farrell critiques the Rockstar Intuition video's tasking as unusable: subjective qualifiers, stacked targets, and one viewer instead of a team." },
        ],
      },
      {
        slug: "2025-06-27-thinking-about-world-war-3",
        mentions: [
          { t: 1862, note: "JT describes his Astro RV project with Morgan and Dan Waites' separate video on the August 9 Mars-Saturn opposition." },
          { t: 9602, note: "JT recounts what the viewer in the Waites Astro RV video saw: China-Taiwan, Russia-Ukraine and Israel-Iran conflicts." },
        ],
      },
      {
        slug: "2025-07-16-human-nature-and-the-paranormal",
        mentions: [
          { t: 594, note: "JT and Morgan Farrell discuss who counts as originators of the Astro-RV Project, with Ingo Swann's Nostradamus Factor raised as precedent." },
          { t: 9521, note: "JT describes Dan Waites tasking Josh Maitland on the August 9 transit and the war, flooding and UFO scenario drawn from it." },
          { t: 14039, note: "JT notes the 'lady' imagery associated with Chris Bledsoe also appearing in Josh Maitland's August 9 Astro-RV material." },
        ],
      },
      {
        slug: "2026-01-11-karmic-deep-impact",
        mentions: [
          { t: 1773, note: "JT argues astrology is an analog simulation model refined over 500 years in Babylon and that psychics and astrologers work well together." },
          { t: 4191, note: "JT describes the Astro RV project of Josh Maitland and Dan Waites, whose session accidentally spanned three years, showing war and flooding." },
        ],
      },
      {
        slug: "2026-01-20-thunderdome-saturn-neptune-and-the-archons",
        mentions: [
          { t: 7005, note: "JT recounts joining the Astro RV Project in 2023, then reading the group's public sessions as hinting at the reality overlay." },
        ],
      },
      {
        slug: "2026-03-19-the-long-emergency",
        mentions: [
          { t: 5441, note: "JT recalls past Astro RV Spaces on this transit and says Josh Maitland and Dan Waites independently saw widespread revolutions." },
          { t: 5834, note: "JT says Intuitive Underground, Josh Maitland's Astro RV work and other viewers all saw a weapon displacing large amounts of water." },
        ],
      },
      {
        slug: "2026-03-27-you-re-screwed-astrology-questions-answered",
        mentions: [
          { t: 4822, note: "JT explains his work with Morgan fusing astrology and remote viewing, using transits as time coordinates to see past 18 months." },
          { t: 4921, note: "JT describes a newer viewer's accidental astro-RV session on the Saturn-Neptune conjunction that he says matched Iran and UFO events." },
        ],
      },
      {
        slug: "2026-04-01-the-return-of-the-king",
        mentions: [
          { t: 429, note: "JT complains that Dan Waites ran another Astro RV experiment without consulting him and Morgan, calling it what they should have done." },
          { t: 4871, note: "JT argues Waites and his viewers are only about five years into astrology and remote viewing, so lack experience." },
        ],
      },
      {
        slug: "2026-04-02-the-against-the-archons-emergent-archetype-in-media",
        mentions: [
          { t: 3091, note: "JT says he consulted on Morgan's Astro RV project, the first attempt to combine astrology and remote viewing to predict events." },
        ],
      },
      {
        slug: "2026-04-05-astro-rv-alert",
        mentions: [
          { t: 570, note: "JT reacts to a new Astro-RV video from Dan Waites of World Astrology Report, noting he and Morgan did the original project." },
          { t: 732, note: "JT says the WAR team tasked April 19 and Mars-Saturn, arguing astrology forecasts periods, not single dates, and they picked wrongly." },
          { t: 1149, note: "JT reads the five WAR remote viewers' sessions, synthesizing a West Coast tower strike and a possible lunar-capsule disaster." },
        ],
      },
      {
        slug: "2026-04-22-suck-it-dan-waites",
        mentions: [
          { t: 3473, note: "JT says he and Morgan Farrell developed Astro RV and criticizes a second project launched by Dan Waites' World Astrology Report." },
          { t: 4729, note: "JT argues Astro RV could narrow remote viewing's multi-year prediction windows and widen what viewers can perceive in the future." },
          { t: 4940, note: "Morgan Farrell says his one-word summary of how Astro RV has gone is disappointment, as it has been treated as a toy." },
        ],
      },
      {
        slug: "2026-04-25-technical-remote-viewing",
        mentions: [
          { t: 2020, note: "JT says sessions in the other team's Astro RV projects work better with short, precise prompts than long narrative tasking." },
          { t: 18764, note: "JT says he wants to promote Astro RV as the ultimate fusion of astrology and remote viewing for forecasting." },
        ],
      },
      {
        slug: "2026-05-02-final-feedback-intuitive-underground-were-right-about-everything",
        mentions: [
          { t: 2705, note: "JT says the Intuitive Underground reports led to his collaboration with Morgan on the Astro RV project." },
        ],
      },
      {
        slug: "2026-07-05-american-disclosure",
        mentions: [
          { t: 4342, note: "JT says an April 2025 Astro-RV project anticipated an interstellar body and a UFO disclosure wave, while noting tension over credit." },
        ],
      },
    ],
  },
  {
    id: "saturn-neptune",
    name: "Saturn–Neptune at 0° Aries",
    summary: "The February 20, 2026 conjunction at the world point, which JT calls the transit of a lifetime.",
    description: "Every episode where JT McCarthy reads the February 2026 Saturn–Neptune conjunction at 0° Aries, the world point, with timestamped mentions.",
    intro: [
      "Saturn and Neptune met at 0° Aries on February 20, 2026, and JT treats it as the governing transit of the era. He calls it a once-in-roughly-6,400-years conjunction at the “world point,” which he reads as the ascendant of the world chart. He argues it marks a crystallization of collective karma, when illusions take concrete form and their consequences come due.",
      "He tracked it for more than a year. That includes forecasts from 2025, the Karmic Deep Impact and Thunderdome Spaces as it approached, and follow-ups on the April Mars trigger and the long unwinding after. The forecasts and the historical parallels are JT's astrological readings.",
    ],
    related: ["mundane-astrology", "eclipses", "vedic-astrology", "astro-rv"],
    episodes: [
      {
        slug: "2025-05-31-astro-rv-project-morgan-farrell",
        mentions: [
          { t: 13963, note: "JT calls the February 2026 conjunction at 0 Aries, the world point, the transit of our lifetime, roughly once in 6,400 years." },
          { t: 14146, note: "JT argues the Great Reset's 2020 to 2035 timeline mirrors a run of Saturn conjunctions with Pluto, Neptune and Uranus." },
        ],
      },
      {
        slug: "2025-06-27-thinking-about-world-war-3",
        mentions: [
          { t: 1201, note: "JT explains the once-in-6,400-years Saturn-Neptune conjunction at zero Aries, the world point, exact February 20, 2026, as a marker of crisis." },
          { t: 1654, note: "JT argues the 2026-27 astrology is not utopian and describes the Pluto-Uranus-Jupiter basket configuration." },
        ],
      },
      {
        slug: "2026-01-11-karmic-deep-impact",
        mentions: [
          { t: 1004, note: "JT introduces 'Karmic Deep Impact': a once-in-6,400-year Saturn-Neptune alignment on February 20 with a roughly three-year orb." },
          { t: 2845, note: "JT argues zero degrees Aries is the world's ascendant, the identity point of reality, so events there shape history for long." },
          { t: 3179, note: "JT argues 36 years of internet self-disclosure can now be scraped and profiled by AI; he calls that the karmic deep impact." },
        ],
      },
      {
        slug: "2026-01-20-thunderdome-saturn-neptune-and-the-archons",
        mentions: [
          { t: 2533, note: "JT argues the US is hit hardest because the Saturn-Neptune conjunction at 0 Aries lands on its natal IC." },
          { t: 6654, note: "JT says the conjunction brings collective delusion and fraud alongside mass awakening, so everyone will think they are awakening." },
          { t: 8994, note: "JT closes by calling this once-in-6,400-years crystallization of karma and reality a go moment to focus on archonic traits." },
        ],
      },
      {
        slug: "2026-03-19-the-long-emergency",
        mentions: [
          { t: 305, note: "JT says the Saturn-Neptune conjunction, exact February 20, signals crisis, as past Saturn-Pluto conjunctions preceded AIDS and the 2020 pandemic." },
          { t: 736, note: "JT argues 0 Aries is the world's ascendant, so a conjunction there steers history for centuries, beyond 2020." },
          { t: 1271, note: "JT turns to Neptune's rulership of swelling and tides, linking the conjunction to pandemic-type events and a UK meningitis cluster." },
        ],
      },
      {
        slug: "2026-03-27-you-re-screwed-astrology-questions-answered",
        mentions: [
          { t: 2023, note: "JT calls the February 20 Saturn-Neptune conjunction the most notable in lifetimes, with Mars crossing zero Aries as trigger." },
          { t: 2200, note: "JT explains zero Aries as the world point and argues an outer-planet conjunction there can shape history for centuries." },
          { t: 3514, note: "JT argues Saturn-Neptune conjunctions in Aries historically coincide with Russia fighting a war, and says none has occurred since antiquity." },
        ],
      },
      {
        slug: "2026-04-01-the-return-of-the-king",
        mentions: [
          { t: 577, note: "JT calls Saturn conjunct Neptune at 0 Aries the biggest astrological event in a century, signifying collapse of global civilization." },
          { t: 2121, note: "JT compares Ketu in Magha with Saturn-Neptune, arguing both strip away illusion, false identities and corrupt relationships." },
        ],
      },
      {
        slug: "2026-04-05-astro-rv-alert",
        mentions: [
          { t: 959, note: "JT argues Mars crossing zero Aries on April 9-10 will activate the recent Saturn-Neptune conjunction, which is still within orb." },
          { t: 1996, note: "JT calls Saturn-Neptune the governing transit of civilizational collapse, with a failed lunar mission as a symbolic bookend to the American century." },
        ],
      },
      {
        slug: "2026-07-05-american-disclosure",
        mentions: [
          { t: 4312, note: "JT ties 3I/ATLAS going public in July 2025 to the near-exact Saturn-Neptune conjunction, a transit he calls rare." },
        ],
      },
      {
        slug: "2026-09-16-the-world-tree-and-the-eclipse-in-leo",
        mentions: [
          { t: 7354, note: "JT recalls that the February Saturn-Neptune conjunction was expected to take years to unwind and connects it to the upheaval in leadership." },
        ],
      },
    ],
  },
  {
    id: "eclipses",
    name: "Eclipses",
    summary: "Why JT treats eclipses as triggers, from Babylonian omens to the August 2026 eclipse in Leo.",
    description: "Episodes where JT McCarthy discusses eclipses in astrology: triggers for outer-planet transits, Babylonian omen lore, and the August 2026 eclipse in Leo.",
    intro: [
      "In JT's working method, eclipses are timing devices. He argues that ordinary new and full moons rarely matter. What tips slow outer-planet transits into events, he says, is an eclipse, or a fast planet like Mars or Jupiter later crossing an eclipse point.",
      "The fullest treatment is The World Tree and the Eclipse in Leo. In it JT traces eclipse lore back to Babylonian omen-watching and its “substitute kings” and explains the 19-year echo of Leo eclipses. He reads the August 12, 2026 eclipse as a changing of the guard. These are interpretive forecasts, not predictions of fact.",
    ],
    related: ["saturn-neptune", "mundane-astrology", "vedic-astrology"],
    episodes: [
      {
        slug: "2025-07-16-human-nature-and-the-paranormal",
        mentions: [
          { t: 9879, note: "JT links the 2017 eclipse and the September 23, 2017 'sign in the sky' to Revelation, calling the eclipse prophetic." },
        ],
      },
      {
        slug: "2026-01-20-thunderdome-saturn-neptune-and-the-archons",
        mentions: [
          { t: 1438, note: "JT says the best tools for timing exact events are eclipses or a fast planet like Mars crossing a long-term outer-planet position." },
          { t: 2437, note: "JT expects acceleration around the eclipse just before the Saturn-Neptune conjunction, which he says may shake the UFOX scene." },
        ],
      },
      {
        slug: "2026-03-27-you-re-screwed-astrology-questions-answered",
        mentions: [
          { t: 831, note: "JT says inner planets and eclipses trigger outer-planet transits, explaining why exact transit dates often show no event." },
          { t: 1682, note: "JT argues ordinary full and new moons rarely matter, but eclipses and their activations can mark life-changing years." },
        ],
      },
      {
        slug: "2026-09-16-the-world-tree-and-the-eclipse-in-leo",
        mentions: [
          { t: 5255, note: "JT traces eclipse astrology to Babylonian omen-watching, arguing eclipses alter the roles of rulers and prominent men, including substitute kings." },
          { t: 5521, note: "JT explains the 19-year echo of Leo eclipses and reads the August 12, 2026 south-node eclipse as a changing of the guard." },
          { t: 5912, note: "JT lays out how Jupiter and Mars crossing the eclipse point, including Mars on election day November 3, would activate it." },
          { t: 6407, note: "JT summarizes his timing for the eclipse activations: around October 3, around November 3, resolving between June 7 and July 12." },
        ],
      },
    ],
  },
  {
    id: "mundane-astrology",
    name: "Mundane Astrology",
    summary: "The astrology of nations and world events: the US chart, Pluto in Aquarius, Uranus in Gemini, war and the oil shock.",
    description: "Episodes on mundane astrology with JT McCarthy: the US chart, Pluto in Aquarius, Uranus in Gemini, war, and the Strait of Hormuz, with timestamped mentions.",
    intro: [
      "Mundane astrology reads charts for nations, events and eras rather than individuals, and JT's mundane forecasting runs through most of the show. His recurring tools are the Sibley chart of the United States and its IC, Pluto's ingress into Aquarius, Uranus entering Gemini (which he calls a “bifurcating” signature), and the Mars triggers he uses to time escalation.",
      "His recurring theme is a protracted crisis: widening war, energy and supply shocks around the Strait of Hormuz, and new limits on mobility. He frames all of it as astrological reading, and often adds that correlation is not causation.",
    ],
    related: ["saturn-neptune", "eclipses", "astro-rv", "disclosure"],
    episodes: [
      {
        slug: "2025-05-31-astro-rv-project-morgan-farrell",
        mentions: [
          { t: 11875, note: "JT says world astrology points to escalating military conflict; Morgan notes Intuitive Underground's separate work on US-China relations." },
          { t: 13825, note: "JT cautions that Andre Barbault's forecast of utopian astro-weather in 2027 and 2028 could still mean worse conditions if war comes first." },
          { t: 14475, note: "JT reads the world-point transit as signalling the end or transformation of a global empire, which he identifies as the United States." },
        ],
      },
      {
        slug: "2025-06-27-thinking-about-world-war-3",
        mentions: [
          { t: 2100, note: "JT argues Pluto's ingress into Aquarius and Uranus entering Gemini, a bifurcating aspect, set up the crisis conditions for a major war." },
          { t: 2540, note: "JT argues Middle East wars are about controlling oil flows to Europe, with Iran's role being to close the Strait of Hormuz." },
          { t: 3000, note: "JT claims foreign-sponsored race-war and civil-war attempts could not happen before Uranus enters Gemini and may only be stalled, not defeated." },
        ],
      },
      {
        slug: "2025-07-16-human-nature-and-the-paranormal",
        mentions: [
          { t: 9641, note: "JT, as an astrologer, expects severe civilizational changes within about a year and a half, including war, coastal flooding and UFOs." },
        ],
      },
      {
        slug: "2026-01-11-karmic-deep-impact",
        mentions: [
          { t: 1125, note: "JT argues Saturn-Neptune in Aries signals war and that Uranus entering Gemini in summer 2026 splits the world into two camps." },
          { t: 4307, note: "JT links the transit's near-exact hit on the US chart's IC to homeland themes, citing Greenland rare earths and Venezuela oil." },
          { t: 4712, note: "JT says Saturn-Neptune conjunctions in Aries have historically coincided with Russian military success, and cautions against misreading that." },
        ],
      },
      {
        slug: "2026-01-20-thunderdome-saturn-neptune-and-the-archons",
        mentions: [
          { t: 1486, note: "JT explains outer-planet ingresses, such as Pluto into Aquarius and October 7, as keys to the period's themes, with Mars as trigger." },
          { t: 1920, note: "JT likens the ICE warrantless-entry memo to the writs-of-assistance grievances of the American Revolution, which he ties to Pluto in Aquarius." },
        ],
      },
      {
        slug: "2026-03-19-the-long-emergency",
        mentions: [
          { t: 3412, note: "JT notes Pluto transiting China's ascendant, which he reads as a period when China is especially dangerous." },
          { t: 3922, note: "JT says the astrology indicates a roughly two-year crisis that would partly resolve, without implying a return to normal." },
        ],
      },
      {
        slug: "2026-03-27-you-re-screwed-astrology-questions-answered",
        mentions: [
          { t: 2630, note: "JT forecasts Uranus entering Gemini around July as a stark global and domestic division, citing the American Revolution and World War II." },
          { t: 3254, note: "JT compares the Civil War to a coming sectarian divide under Uranus in Gemini, framing both sides as crusades." },
          { t: 6831, note: "JT argues Pluto's move into Aquarius, around October 7, coincided with religious crusades and a widening Middle East conflict." },
        ],
      },
      {
        slug: "2026-04-01-the-return-of-the-king",
        mentions: [
          { t: 640, note: "JT lays out his Saturn-Neptune forecast of an oil-infrastructure collapse, war involving Russia, and shortages after April 15." },
          { t: 1693, note: "JT argues the coming crisis, including shortages of fuel, food and medicine, follows from corrupt behavior, citing Epstein as an example." },
        ],
      },
      {
        slug: "2026-04-05-astro-rv-alert",
        mentions: [
          { t: 2148, note: "JT says the Saturn-Neptune conjunction fell on the IC of the US Sibley chart, which he reads as the nation's physical land." },
          { t: 2346, note: "JT discusses the Iran war and possible US retaliation, dismissing reflexive false-flag speculation." },
          { t: 2680, note: "JT warns of oil shortages after mid-April and demand destruction, and says a prolonged blackout is his biggest concern." },
        ],
      },
      {
        slug: "2026-04-22-suck-it-dan-waites",
        mentions: [
          { t: 4172, note: "JT argues the nuclear-age mundane chart was a poor choice for Dan Waites' Astro RV session because it needed natal-style targeting." },
          { t: 4444, note: "JT stands by April 11-12 as the real pivot point, citing later pipeline explosions and earthquakes in Japan." },
        ],
      },
      {
        slug: "2026-04-25-technical-remote-viewing",
        mentions: [
          { t: 19122, note: "JT says a global crisis is already underway, citing a fuel crisis and escalating world war, though it may unfold slowly." },
        ],
      },
      {
        slug: "2026-05-08-disclosure-and-technical-remote-viewing",
        mentions: [
          { t: 2089, note: "JT says the 1800s Neptune-Pluto conjunction coincided with the occult revival and the start of UFO airship sightings." },
        ],
      },
      {
        slug: "2026-07-05-american-disclosure",
        mentions: [
          { t: 4282, note: "JT says global upheaval such as Hormuz closing and Greenland talk began correlating with 3I/ATLAS, while noting correlation is not causation." },
        ],
      },
      {
        slug: "2026-09-16-the-world-tree-and-the-eclipse-in-leo",
        mentions: [
          { t: 6646, note: "JT argues the Middle East war, Ukraine and the fuel crisis are one escalating war that will limit physical and social mobility." },
          { t: 7354, note: "JT ties the coming limits on mobility to the astrological picture of a major civilizational shift in leadership and social roles." },
        ],
      },
    ],
  },
  {
    id: "vedic-astrology",
    name: "Vedic Astrology",
    summary: "Ketu in Magha, the nakshatras, Kali Yuga and moksha: where JT borrows from jyotish.",
    description: "Episodes where JT McCarthy draws on Vedic astrology: Ketu in Magha nakshatra, Rahu and Ketu, Kali Yuga and moksha, with timestamped mentions.",
    intro: [
      "JT works mostly in Western astrology and says plainly that he isn't a Vedic astrologer. Still, he keeps returning to jyotish where he thinks it sees further: the lunar nodes Rahu and Ketu, the nakshatras (lunar mansions), the yugas, and moksha as the goal of release.",
      "The centerpiece is The Return of the King, co-hosted with Melissa. It reads Ketu's transit through Magha nakshatra as the Vedic mirror of Saturn–Neptune in Aries. Other episodes cover Ketu and the royal star Regulus, sacred time and the Great Year, and checking your own nodes for guidance on moksha. The readings are JT's and his co-hosts'.",
    ],
    related: ["saturn-neptune", "eclipses", "the-hierarchy", "archons"],
    episodes: [
      {
        slug: "2026-03-27-you-re-screwed-astrology-questions-answered",
        mentions: [
          { t: 9892, note: "JT reads a contactee's jumbled prediction through Vedic astrology, citing Ketu, Regulus and Mars crossing zero Aries around Orthodox Easter." },
        ],
      },
      {
        slug: "2026-04-01-the-return-of-the-king",
        mentions: [
          { t: 168, note: "JT introduces Ketu's transit through Magha Nakshatra as a window for ancestral karma and inner work this year." },
          { t: 1201, note: "JT explains Ketu as the karma to work through toward moksha, contrasting Vedic and Western treatments of the lunar nodes." },
          { t: 1987, note: "JT links the transit to a late Kali Yuga phase where angels and demons share bodies, with corruption being exposed." },
        ],
      },
      {
        slug: "2026-04-25-technical-remote-viewing",
        mentions: [
          { t: 14382, note: "JT ties earlier moksha-themed spaces to Vedanta and his recent astrology spaces on the astrology of moksha." },
          { t: 21866, note: "JT suggests checking one's lunar mansions and Ketu for guidance on moksha, saying the Vedic tradition has the expertise." },
        ],
      },
      {
        slug: "2026-04-29-oriental-archons",
        mentions: [
          { t: 3029, note: "JT says Vedic scholars inflated the Great Year of precession by a factor of 360 to represent sacred time, complicating timeline reconciliation." },
        ],
      },
      {
        slug: "2026-09-16-the-world-tree-and-the-eclipse-in-leo",
        mentions: [
          { t: 4859, note: "JT says he is not pro-Vedic astrology but grants that the nakshatras and nodes, Rahu and Ketu, capture unconscious influence." },
          { t: 5719, note: "JT places the south node, Ketu, over the royal star Regulus, while saying he is not a Vedic astrologer." },
        ],
      },
    ],
  },
  {
    id: "simulation",
    name: "The Simulation",
    summary: "JT's “reality overlay”: simulation on biological hardware, from the Gnostics and Philip K. Dick to Cortical Labs.",
    description: "Simulation theory as JT McCarthy frames it: a reality overlay on biological hardware, Philip K. Dick, Cortical Labs and remote-viewing data, with timestamps.",
    intro: [
      "JT calls himself a simulationist, though he usually prefers the term “reality overlay.” His version isn't a silicon computer game. He describes a Matrix-style dream generated on a network of living brains, and traces the idea through Nick Bostrom and Philip K. Dick back to Buddhist, Hindu, Greek, Gnostic and Manichaean sources.",
      "In these episodes he and his guests set Intuitive Underground's remote-viewing descriptions of the overlay beside ancient texts. They also discuss Cortical Labs' brain-cell computers, which JT presents as “final feedback,” and the simulation as an emerging archetype in fiction. These are speculative arguments, offered as JT's and his guests' views.",
    ],
    related: ["archons", "technical-remote-viewing", "psychic-gene", "disclosure"],
    episodes: [
      {
        slug: "2025-05-28-bigfoot-state-of-reality-morgan-dan",
        mentions: [
          { t: 3866, note: "The viewers explain consciousness as fundamental, adversaries hijacking soul energy, and a technological false-reality overlay powered by it." },
          { t: 10795, note: "JT argues the false-reality overlay makes sense of UFO abduction oddities such as people appearing, walking through walls and floating." },
          { t: 12500, note: "A guest notes that inside a reality overlay you cannot trust your senses or even your thoughts, since thought is a perception." },
        ],
      },
      {
        slug: "2025-05-31-astro-rv-project-morgan-farrell",
        mentions: [
          { t: 5860, note: "JT argues astrology is an analog simulation model built over centuries in Mesopotamia, comparable to digital simulations like the Sentient World Simulation." },
          { t: 13502, note: "JT shares a link on the Sentient World Simulation, which he describes as a DoD-funded project at an Indiana university." },
        ],
      },
      {
        slug: "2025-06-27-thinking-about-world-war-3",
        mentions: [
          { t: 1245, note: "JT argues the planet, or the simulation, has an astrological chart and that zero Aries is its world ascendant." },
          { t: 12730, note: "A speaker argues remote-viewing data suggests a reality overlay and sorts non-human intelligences by whether they are inside or outside the simulation." },
          { t: 13201, note: "The speakers debate whether astral bodies exist outside the simulation, one saying reincarnation happens entirely within the overlay." },
        ],
      },
      {
        slug: "2025-07-16-human-nature-and-the-paranormal",
        mentions: [
          { t: 863, note: "JT says he and Morgan hold that we live in a false reality, preferring 'reality overlay' over 'simulation' or 'matrix'." },
          { t: 5970, note: "The discussion turns to Nassim Haramein's feedback-mechanism argument, with the claim that neural tissue and organoids may outperform trained AI." },
          { t: 13634, note: "JT and Morgan weigh 'collective dream' against matrix and overlay, describing a networked mental construct possibly regulated by technology." },
        ],
      },
      {
        slug: "2026-01-11-karmic-deep-impact",
        mentions: [
          { t: 1853, note: "JT prefers the term 'reality overlay' to simulation or matrix and says session material supports it." },
          { t: 2408, note: "JT says civilizations throughout history described the world as illusory, which he frames as the reality overlay." },
        ],
      },
      {
        slug: "2026-01-20-thunderdome-saturn-neptune-and-the-archons",
        mentions: [
          { t: 3045, note: "JT identifies the Apocryphon of John as the text describing what he calls the reality overlay, or matrix simulation." },
          { t: 9448, note: "JT ties a clairvoyant's reality-overlay account to the Gospel of Thomas and Musk's argument that a simulation conserves the most unusual outcome." },
        ],
      },
      {
        slug: "2026-01-27-the-empire-never-ended-secret-of-the-psychic-gene",
        mentions: [
          { t: 2041, note: "JT argues ancient cultures called the world an illusion or reality overlay, tracing modern simulation ideas to Philip K. Dick." },
          { t: 2301, note: "JT describes Dick's belief that the Black Iron Prison was built around early Christians and that the Roman empire never ended." },
        ],
      },
      {
        slug: "2026-03-27-you-re-screwed-astrology-questions-answered",
        mentions: [
          { t: 7861, note: "JT maps Pluto, Neptune and Uranus onto the simulation, with Uranus as the awakener to an artificial reality." },
          { t: 8625, note: "JT argues the reality overlay exists to produce emergent solutions to problems, tying it to natural selection and suffering." },
          { t: 9187, note: "JT links remote viewing data and the computers made from human brain cells to his claim that we run on biological hardware." },
        ],
      },
      {
        slug: "2026-04-01-the-return-of-the-king",
        mentions: [
          { t: 2293, note: "JT argues Hinduism treats reality as a simulation and reads the Pitris as the original inhabitants of the reality overlay." },
        ],
      },
      {
        slug: "2026-04-02-the-against-the-archons-emergent-archetype-in-media",
        mentions: [
          { t: 2746, note: "JT traces dungeon-core fiction's focus on simulation theory and compares its details with remote-viewing session data on prisoners powering a simulation." },
          { t: 3739, note: "JT proposes the Intuitive Underground data describes a simulation run in networked brains, citing Cortical Labs' brain-cell computers playing Doom." },
        ],
      },
      {
        slug: "2026-04-22-suck-it-dan-waites",
        mentions: [
          { t: 463, note: "JT argues simulation theory is usually misunderstood: if events happen in minds, it's a computer-generated dream running on an actual biological system." },
          { t: 680, note: "JT notes news of computers running on cloned human brain cells broke after his talks, and ties the boxes to abduction reports." },
          { t: 2168, note: "JT argues life is full of suffering because the simulation's goal is solving problems, so every event carries a problem." },
        ],
      },
      {
        slug: "2026-04-25-technical-remote-viewing",
        mentions: [
          { t: 402, note: "JT says a conversation about AI raised his confidence in simulationism and the reality overlay." },
          { t: 7620, note: "JT argues the simulation is growing more information-dense, with technology and AI as mirrors of consciousness." },
          { t: 8671, note: "JT, as a self-described simulationist, says a simulation exists to produce emergent solutions to problems, comparing it to natural selection." },
          { t: 23442, note: "JT, a self-described simulationist, doubts any outside universe wants us, answering a guest's talk of a biological quarantine." },
        ],
      },
      {
        slug: "2026-04-29-oriental-archons",
        mentions: [
          { t: 5324, note: "JT says DMT-plus-laser experimenters report Matrix-like code resembling Japanese kanji, and asks whether the overlay's technology originated in Asia." },
          { t: 6095, note: "JT argues that if reality is a simulation, we should look in the historical record for residual evidence resembling base-level reality." },
        ],
      },
      {
        slug: "2026-05-02-final-feedback-intuitive-underground-were-right-about-everything",
        mentions: [
          { t: 3618, note: "JT recounts finding Cortical Labs, an Australian firm selling $35,000 computers of human brain cells taught Pong and then Doom." },
          { t: 3973, note: "JT announces Cortical Labs data centers of brain-cell pods as final feedback, which he says matches Intuitive Underground's session descriptions." },
          { t: 6897, note: "JT speculates about future virtual worlds with sentient NPCs run by brain-cell computers, and what that implies for a reality overlay." },
        ],
      },
      {
        slug: "2026-05-08-disclosure-and-technical-remote-viewing",
        mentions: [
          { t: 986, note: "JT argues the simulation is biological and runs on actual people, so humans were hijacked rather than created by aliens." },
          { t: 1706, note: "JT says beings outside the reality overlay, nicknamed the 'space dicks' by the Intuitive Underground group, are one or more interstellar factions." },
          { t: 4766, note: "JT argues periodic cataclysms reboot the simulation, with data harvested and stored before restart, and the world grows stranger approaching it." },
          { t: 6495, note: "JT explains Cortical Labs' human brain-cell organoids playing Pong and Doom as a miniature proof of concept for the simulation he describes." },
        ],
      },
      {
        slug: "2026-07-04-the-revelation-of-the-hierarchy",
        mentions: [
          { t: 1252, note: "JT asserts we live in a simulation on biological hardware, not a computer, tracing the idea from Bostrom to antiquity." },
          { t: 2228, note: "JT discusses simulationism on biological hardware as an interface between computers and bodies, and the map of the simulation's hidden dimensions." },
          { t: 5231, note: "JT says the simulation is now the dominant emerging archetype across TV, influencers and academics." },
        ],
      },
      {
        slug: "2026-07-05-american-disclosure",
        mentions: [
          { t: 3374, note: "JT says simulationism is the third branch of disclosure, citing ancient sources and remote-viewing data that point to extraterrestrial creators." },
          { t: 4072, note: "JT argues that if reality is an extension of collective consciousness, an interstellar object like 3I/ATLAS must carry meaning." },
        ],
      },
      {
        slug: "2026-09-09-intuitive-underground-and-the-power-of-remote-viewing",
        mentions: [
          { t: 4116, note: "Morgan Farrell says a 'most significant target' session pointed to a simulation with a biological component, closer to a shared, regulated dream." },
          { t: 4473, note: "JT places the simulation idea in Buddhism, Hinduism, Greek antiquity, the Gnostics and the Manichaeans." },
        ],
      },
      {
        slug: "2026-09-16-the-world-tree-and-the-eclipse-in-leo",
        mentions: [
          { t: 2960, note: "JT argues the simulation's injustice persists because natural selection and animal farming externalize suffering onto others, sustaining the system." },
          { t: 3497, note: "JT argues the simulation is an emerging archetype in fiction and complains that tech bros have appropriated simulationism." },
        ],
      },
    ],
  },
  {
    id: "disclosure",
    name: "Disclosure",
    summary: "UFO disclosure as JT reads it: eschatology, propaganda, 3I/ATLAS, and what he thinks the real secret is.",
    description: "UFO disclosure episodes with JT McCarthy and guests: American eschatology, 3I/ATLAS, Chris Bledsoe and remote-viewing takes on UAP, with timestamps.",
    intro: [
      "JT is skeptical of the mainstream disclosure story but takes the phenomenon seriously. Across these episodes he reads UFOs as Cold War signaling, as American eschatology (a Puritan-versus-Baptist argument carried on through the alien question), and as one more face of the reality overlay.",
      "His recurring argument, developed with Morgan Farrell, is that the real secret isn't simply that aliens exist. In his view, it's that humanity was hijacked into a biological simulation. Along the way he takes on 3I/ATLAS, Chris Bledsoe's predictions and the evangelical “demonic disclosure” narrative. All of this is presented as JT's and his guests' interpretation.",
    ],
    related: ["ufox", "simulation", "technical-remote-viewing", "the-hierarchy"],
    episodes: [
      {
        slug: "2025-05-28-bigfoot-state-of-reality-morgan-dan",
        mentions: [
          { t: 3212, note: "A speaker cites a psychologist who studies UFO abductees to argue the beings are checking up on a continuing genetic project." },
          { t: 8031, note: "JT says abductee accounts and government whistleblower limited hangouts point toward the same story the viewers' data tells." },
        ],
      },
      {
        slug: "2025-05-31-astro-rv-project-morgan-farrell",
        mentions: [
          { t: 6761, note: "A caller asks whether Astro RV could time UAP disclosure; JT and Morgan call it very complicated, as disclosure lacks a definition." },
          { t: 10468, note: "The conversation turns to Chris Bledsoe's Regulus prediction and why the UFO phenomenon draws ridicule, with JT weighing what astrology could assess." },
        ],
      },
      {
        slug: "2025-06-27-thinking-about-world-war-3",
        mentions: [
          { t: 395, note: "JT says the UFO phenomenon was long suggested to work as Cold War propaganda shaping opinion about nuclear weapons." },
          { t: 9704, note: "JT argues UFOs would appear if nations exchange missiles and reads the disclosure wave as nations signaling capabilities." },
          { t: 11944, note: "JT argues no one should trust predictions from purported non-human intelligences and says a bedroom visitor delivering messages should be discounted entirely." },
        ],
      },
      {
        slug: "2025-07-16-human-nature-and-the-paranormal",
        mentions: [
          { t: 1103, note: "JT and Morgan discuss UFO craft and beings as possible virtual avatars from outside the overlay, tying in Keel and Vallee." },
          { t: 1647, note: "JT cites Gods of Eden, Whitley Strieber and Virgin Mary abduction reports as easier to explain under the overlay model." },
          { t: 7173, note: "JT suggests extraterrestrial beings may be non-player-character-like constructs inside the overlay, or enslaved beings from base reality." },
        ],
      },
      {
        slug: "2026-01-11-karmic-deep-impact",
        mentions: [
          { t: 5272, note: "JT says UFO-community predictions of a 2026 spiritual unfolding may be grifters repackaging astrological forecasts as extraterrestrial prophecy." },
          { t: 6817, note: "JT recounts treating 3I/ATLAS as an eschatological sign more than an alien question, and how the narrative around it shifted." },
        ],
      },
      {
        slug: "2026-03-19-the-long-emergency",
        mentions: [
          { t: 5504, note: "JT says the Astro RV sessions included 'tons of UFOs', fitting older predictions that UFOs would appear during the next global war." },
        ],
      },
      {
        slug: "2026-03-27-you-re-screwed-astrology-questions-answered",
        mentions: [
          { t: 9840, note: "JT discusses Chris Bledsoe's predicted new knowledge and NHI contact, with remote viewers saying he had a real experience." },
        ],
      },
      {
        slug: "2026-04-01-the-return-of-the-king",
        mentions: [
          { t: 1794, note: "JT discusses contactee Chris Bledsoe's predictions about Easter 2026 and Regulus, and notes Magha is ruled by Regulus." },
        ],
      },
      {
        slug: "2026-04-22-suck-it-dan-waites",
        mentions: [
          { t: 1719, note: "JT proposes that some UFO abduction memories are screen memories concealing a real event involving real people, possibly under anesthesia." },
        ],
      },
      {
        slug: "2026-04-29-oriental-archons",
        mentions: [
          { t: 3943, note: "JT recalls whistleblowers telling Congress the entities were deep-ocean dwellers, before the aliens-or-demons framing, which he calls a psyop." },
        ],
      },
      {
        slug: "2026-05-02-final-feedback-intuitive-underground-were-right-about-everything",
        mentions: [
          { t: 10860, note: "The discussion covers a study on ancient human hybridization that the UFO community misread as confirming alien hybridization." },
        ],
      },
      {
        slug: "2026-05-07-ufox-the-crusade-within-ufology",
        mentions: [
          { t: 2860, note: "JT recounts evangelical pastors claiming intelligence insiders said disclosure would reveal demonic UFOs, then argues the government's own story is physical aliens." },
          { t: 3380, note: "A speaker argues any government disclosure of alien technology would likely be deception, since it would also inform China and Russia." },
          { t: 5190, note: "A speaker warns against adopting an 'angels and demons' overlay for the phenomenon, saying it will be weaponized." },
        ],
      },
      {
        slug: "2026-05-08-disclosure-and-technical-remote-viewing",
        mentions: [
          { t: 922, note: "JT argues disclosure's primary secret is that humans were created by God and hijacked by aliens, reading the Carter story as spin." },
          { t: 1862, note: "JT describes the remote viewing community's split over 3I/ATLAS: viewers reported aliens inside it, none, or aliens on another layer of reality." },
          { t: 5159, note: "JT argues nearly every source, except Greer-style channelers, describes non-human experimentation, so disclosure is bad news and officials break down." },
        ],
      },
      {
        slug: "2026-07-04-the-revelation-of-the-hierarchy",
        mentions: [
          { t: 768, note: "JT says the revelation of the hierarchy includes the revelation of UFOs and extraterrestrial levels of governance above humanity." },
        ],
      },
      {
        slug: "2026-07-05-american-disclosure",
        mentions: [
          { t: 2431, note: "JT argues UFO disclosure is really eschatology, end-times belief shaped by Puritan theology, with aliens cast as judging angels." },
          { t: 2957, note: "JT says Southern Baptist culture reads the whole UFO phenomenon as demonic deception, citing the Collins Elite inside the Pentagon." },
          { t: 3651, note: "JT and Matt speculate about 3I/ATLAS passing close to Mars and Jupiter, and about amphibious beings and Europa." },
        ],
      },
      {
        slug: "2026-09-09-intuitive-underground-and-the-power-of-remote-viewing",
        mentions: [
          { t: 5558, note: "JT argues some prominent UFO whistleblowers have remote-viewing training, so their testimony may not be what it seems." },
        ],
      },
      {
        slug: "2026-09-16-the-world-tree-and-the-eclipse-in-leo",
        mentions: [
          { t: 5680, note: "JT links the royal star Regulus to Chris Bledsoe's ufological predictions and says he'll do an episode to set that record straight." },
        ],
      },
    ],
  },
  {
    id: "ufox",
    name: "UFOx",
    summary: "JT's running critique of the UFOx scene on X: its creators, its drama, and the Catholic surge in ufology.",
    description: "Episodes where JT McCarthy critiques the UFOx ufology scene on X: its creators, its drama and the Catholic surge in ufology, with timestamped mentions.",
    intro: [
      "UFOx is the loose network of ufology Spaces and creators on X. JT drifted into its orbit, as he tells it, by way of the Doom Room, and he has never claimed it as his own. His critique has stayed consistent. He says many of its creators don't actually believe in aliens, that newcomers get “cocooned” by a handful of hosts, and that the scene runs on drama more than inquiry.",
      "UFOx: The Crusade Within Ufology is the full-length treatment and looks at the sudden Catholic surge in ufology. Other episodes catch the scene's flare-ups as they happened. These are JT's opinions about a community, and guests on the panel sometimes disagree.",
    ],
    related: ["disclosure", "technical-remote-viewing", "archons"],
    episodes: [
      {
        slug: "2025-07-16-human-nature-and-the-paranormal",
        mentions: [
          { t: 1013, note: "JT says his overlay view of the UFO phenomenon differs from how many in the UFOX scene read it." },
          { t: 10737, note: "JT warns of rising cognitive aggression in the UFOX community and a looming crisis, discussing the Rogers coin fallout." },
          { t: 15245, note: "JT floats using the Roswell event as a natal chart to track and predict UFOX community drama." },
        ],
      },
      {
        slug: "2026-01-20-thunderdome-saturn-neptune-and-the-archons",
        mentions: [
          { t: 276, note: "JT recounts drifting into the UFOX orbit via the Doom Room and argues its content creators do not actually believe in aliens." },
          { t: 2486, note: "JT forecasts that a prominent male UFOX figure may leave the scene around the coming eclipse, citing UFOX's natal Mars." },
        ],
      },
      {
        slug: "2026-03-27-you-re-screwed-astrology-questions-answered",
        mentions: [
          { t: 6872, note: "JT says some in the UFOx scene show AI-induced delusion, linking it to Pluto in Aquarius transits." },
        ],
      },
      {
        slug: "2026-04-29-oriental-archons",
        mentions: [
          { t: 384, note: "JT opens on the latest UFOX drama, a podcast host's cancellation, and says he has heard little new in these spaces." },
          { t: 1315, note: "JT criticizes UFOX spaces for what he calls Puritanism, citing backlash over the word oriental and over a Hopi prophecy space." },
        ],
      },
      {
        slug: "2026-05-02-final-feedback-intuitive-underground-were-right-about-everything",
        mentions: [
          { t: 224, note: "JT disavows any UFOX affiliation and condemns how, in his view, the scene treated women who came forward." },
          { t: 11457, note: "A speaker recounts how UFOX grew out of late-night radio fringe stories and discusses the recurring crab-people meme." },
        ],
      },
      {
        slug: "2026-05-07-ufox-the-crusade-within-ufology",
        mentions: [
          { t: 608, note: "JT opens by noting two words, 'interdimensional' and 'Catholic', suddenly recurring in UFOX and ufology spaces, and sets up the thesis." },
          { t: 2825, note: "JT argues Mav's and Gene Stickle's spaces now eclipse UFOX, which he calls mostly drama at present." },
          { t: 3900, note: "JT describes newcomers being 'cocooned' by the same handful of UFOX hosts, who co-host and spin the narrative, citing the pastor example." },
          { t: 11226, note: "The panel debates whether a few prominent UFOX hosts act as gatekeepers, with guests on both sides." },
        ],
      },
      {
        slug: "2026-05-08-disclosure-and-technical-remote-viewing",
        mentions: [
          { t: 3166, note: "JT argues ufology factions (plasma beings, angels and demons) are siloed by confirmation bias, so released documents will not matter." },
          { t: 3701, note: "JT criticizes UFOX and online ufology for obsessing over classified military secrets, suggesting large pushing crowds include foreign intelligence assets." },
        ],
      },
    ],
  },
  {
    id: "the-hierarchy",
    name: "The Revelation of the Hierarchy",
    summary: "The Theosophical prophecy JT builds Peak Mind around: Kalki, an interstellar object in 2025, and the Pitris.",
    description: "The revelation of the hierarchy as JT McCarthy reads it: Theosophy, the Kalki avatar, an interstellar object in 2025 and the Pitris, with timestamps.",
    intro: [
      "“The revelation of the hierarchy” is JT's name for a forecast he inherits from Theosophy. He calls Theosophy the last great clairvoyant community, born when Western Europeans reached Tibet in the 1860s. As he reads it, Theosophists of the 1920s and 30s anticipated an interstellar object arriving around 2025, carrying the Kalki avatar and triggering a civilizational reset.",
      "He describes the revelation as twofold. The “gods,” which he calls the archons, return to human awareness, and a hidden network of governance among humans comes to light. He also reinterprets the Hindu Pitris as the original personalities seeded into the simulation. He keeps his distance from Alice Bailey's “externalization of the hierarchy” and from Theosophy's Luciferian drift, even as he draws on the material.",
    ],
    related: ["archons", "simulation", "psychic-gene", "vedic-astrology"],
    episodes: [
      {
        slug: "2026-01-11-karmic-deep-impact",
        mentions: [
          { t: 6931, note: "JT rejects Alice Bailey's 'externalization of the hierarchy' and Theosophy's Luciferian drift, yet notes her comet prediction and links it to Bledsoe." },
        ],
      },
      {
        slug: "2026-04-01-the-return-of-the-king",
        mentions: [
          { t: 2260, note: "JT describes the Vedic Pitris as luminous ancestors and equates them with the sleepers who underpin the reality overlay." },
        ],
      },
      {
        slug: "2026-04-29-oriental-archons",
        mentions: [
          { t: 3262, note: "JT says Tibetan libraries hold about 100,000 untranslated texts and that Theosophy sprang from translating a couple of them in the mid-1800s." },
          { t: 5017, note: "JT says Western esotericism, like Count St. Germain's story, traces to an immortal brotherhood in the East, plus Taoist immortality traditions." },
        ],
      },
      {
        slug: "2026-07-04-the-revelation-of-the-hierarchy",
        mentions: [
          { t: 273, note: "JT explains the revelation of the hierarchy as a Theosophical prediction, tracing Theosophy to Westerners reaching Tibet in the 1860s." },
          { t: 459, note: "JT says Theosophists predicted a 2025 interstellar comet that is the Kalki avatar on a higher dimension, and links it to Revelation." },
          { t: 702, note: "JT describes the second part of the revelation as exposing an internal network of governance among humans behind the scenes." },
          { t: 1836, note: "JT explains the Pitris, a Hindu term for divine ancestors, as the original personalities involved in the simulation." },
        ],
      },
      {
        slug: "2026-07-05-american-disclosure",
        mentions: [
          { t: 4192, note: "JT recalls the prior week's discussion of Alice Bailey and the Theosophists predicting an interstellar object in 2025, linked to Kalki." },
        ],
      },
    ],
  },
  {
    id: "psychic-gene",
    name: "The Psychic Gene",
    summary: "Dean Radin's psychic-gene study, the Gnostic hylic–psychic–pneumatic split, and the NPC debate.",
    description: "Episodes where JT McCarthy discusses the Dean Radin psychic-gene study, the Gnostic hylic, psychic and pneumatic types, and the NPC debate, with timestamps.",
    intro: [
      "JT keeps coming back to a genetics study associated with Dean Radin and the Institute of Noetic Sciences. As he reads it, the study found a mutation that correlates with the absence of psychic perception, not its presence. He says roughly 40% of people carry it and that it centers geographically on Rome. He argues the mutation suppresses an ancient retrovirus, which suggests to him that psychic ability was acquired.",
      "He ties this to the Gnostic division of humanity into hylic, psychic and pneumatic types, and to the modern “NPC” discourse. He argues the term isn't inherently a slur, and that the people who lack the sense “are us and we are them.” The genetics and the interpretation are JT's reading of the research, not settled science.",
    ],
    related: ["simulation", "archons", "the-hierarchy"],
    episodes: [
      {
        slug: "2026-01-27-the-empire-never-ended-secret-of-the-psychic-gene",
        mentions: [
          { t: 185, note: "JT introduces the Dean Radin 23andMe study and argues its mutation blocks psychic ability rather than grants it, clustering around Rome." },
          { t: 714, note: "JT says the mutation's documented function is suppressing recently acquired endogenous retroviruses, so he argues psychic ability arrived through a retrovirus." },
          { t: 4935, note: "JT connects the gene to the Gnostic hylic, psychic and pneumatic types, proposing it as a genetic marker for hylics." },
        ],
      },
      {
        slug: "2026-03-19-the-long-emergency",
        mentions: [
          { t: 6710, note: "JT says the Gnostics held there are three types of people, and that psychics are capable of great good and great evil." },
        ],
      },
      {
        slug: "2026-04-22-suck-it-dan-waites",
        mentions: [
          { t: 548, note: "JT describes how simulation theorists imagine some people as players and others as NPCs generated by the computer, and critiques the idea." },
        ],
      },
      {
        slug: "2026-05-02-final-feedback-intuitive-underground-were-right-about-everything",
        mentions: [
          { t: 8677, note: "JT explains Dean Radin's psychic-gene study and argues the mutation blocks retrovirus-driven gene expression, so psychic ability may be acquired." },
        ],
      },
      {
        slug: "2026-05-08-disclosure-and-technical-remote-viewing",
        mentions: [
          { t: 11577, note: "JT recounts a Dean Radin-linked search for a psychic gene, saying it found a mutation in non-psychic people, and speculates on implications." },
        ],
      },
      {
        slug: "2026-07-04-the-revelation-of-the-hierarchy",
        mentions: [
          { t: 2554, note: "JT explains the Gnostic tripartite nature of man (hylic, psychic, pneumatic) as the ancestor of the modern NPC concept." },
          { t: 2792, note: "JT cites Dean Radin and the Institute of Noetic Sciences on a mutation in about 40% of people lacking psychic perception." },
          { t: 3104, note: "JT argues the term NPC isn't inherently dehumanizing and that people lacking this sense are 'us and we are them'." },
        ],
      },
      {
        slug: "2026-09-09-intuitive-underground-and-the-power-of-remote-viewing",
        mentions: [
          { t: 4560, note: "JT argues about 40% of people lack extrasensory perception, often along with metacognition and empathy, and are over-represented among leaders." },
        ],
      },
    ],
  },
];

export function getTopic(id: string): Topic | undefined {
  return TOPICS.find((t) => t.id === id);
}

/** Topics that list the given episode, in TOPICS order. */
export function topicsForEpisode(slug: string): Topic[] {
  return TOPICS.filter((t) => t.episodes.some((e) => e.slug === slug));
}

/** 754 → "12:34", 5025 → "1:23:45" (matches the audio player's clock). */
export function formatTimestamp(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = String(s % 60).padStart(2, "0");
  return h > 0 ? `${h}:${String(m).padStart(2, "0")}:${sec}` : `${m}:${sec}`;
}
