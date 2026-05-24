// Static site data — recurring series and consultation offerings.
// These don't live in a content collection (yet); they're hand-curated.

export const SERIES = [
  {
    id: "archons",
    name: "Against the Archons",
    cadence: "Thursdays",
    blurb: "A weekly walk through the architecture of the cage.",
  },
  {
    id: "ufox",
    name: "UFOx Crusade",
    cadence: "Irregular",
    blurb: "Phenomenon, deception, and the long con of contact.",
  },
  {
    id: "drv",
    name: "Defining Remote Viewing",
    cadence: "Monthly",
    blurb: "The Dames lineage, the protocols, the boundary conditions.",
  },
  {
    id: "astrorv",
    name: "Astro-RV Project",
    cadence: "As targets allow",
    blurb: "Astrology as a targeting layer for blind inquiry.",
  },
  {
    id: "karmic",
    name: "Karmic Deep Impact",
    cadence: "Quarterly",
    blurb: "Mundane charts and the wounds that keep returning.",
  },
];

export const CONSULTS = [
  {
    id: "natal",
    title: "Natal Chart Reading",
    length: "90 min",
    price: "$340",
    pitch: "A first pass at the chart you were born into.",
    body: "We work through the natal chart end to end — luminaries, angles, lordships, and the two or three signatures I think will be load-bearing for the next decade. You leave with a recording, a chart packet, and a short written follow-up.",
    points: [
      "90-minute live session, recorded",
      "Chart packet + written follow-up",
      "One round of email questions after",
    ],
  },
  {
    id: "astrorv",
    title: "Astro-RV Targeting Session",
    length: "60 min",
    price: "$260",
    pitch: "Astrology as a targeting layer for a remote viewing inquiry.",
    body: "You bring a question. We use the chart — yours, the moment's, or a third party's — to fix a target window and a frame. This is not a reading and it is not a viewing; it is the part where the two meet and decide where to point.",
    points: [
      "For practitioners and the curious alike",
      "We define one target and one window",
      "Includes a written tasking document",
    ],
  },
  {
    id: "forecast",
    title: "Annual Forecast",
    length: "2 hr",
    price: "$520",
    pitch: "Transits for the year ahead, framed against your natal chart.",
    body: "Twelve months, walked carefully. Outer planet transits, the two solar returns, the eclipse pair, and the one or two windows where the year actually turns. Heavier on framing than prediction — but framing is what you came for.",
    points: [
      "Two-hour session, recorded",
      "Month-by-month written timeline",
      "Two follow-up emails over the year",
    ],
  },
];

// Deterministic cover-variant rotation for episodes that don't carry their own.
const COVER_VARIANTS = ["amber", "ring", "rule", "disc", "eclipse"] as const;
export type CoverVariant = (typeof COVER_VARIANTS)[number];

export function coverVariantForIndex(i: number): CoverVariant {
  return COVER_VARIANTS[i % COVER_VARIANTS.length];
}
