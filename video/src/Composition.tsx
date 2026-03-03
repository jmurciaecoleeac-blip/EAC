import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Background} from './Background';
import {LogoTitle} from './LogoTitle';
import {EventTitle} from './EventTitle';
import {DateBlock} from './DateBlock';
import {AddressBlock} from './AddressBlock';
import {CTAButton} from './CTAButton';

// Main orchestration component — 3-act structure over 450 frames (15s @ 30fps)
//
// ACT 1 (frames   0– 60): Background sweeps in. Scene is establishing.
// ACT 2 (frames  60–360): Content reveals staggered — EAC → title → date → CTA.
// ACT 3 (frames 360–450): Elements fade out in reverse. Only EAC glows at the end.
//
// Timing constants (single source of truth for all entrance/exit frames):

// ACT 1 — Background
const BG_ENTRANCE = 0;

// ACT 2 — Content entrances
const EAC_ENTRANCE = 62;
const TITLE_ENTRANCE = 82; // first word
const DIVIDER_FRAME = 128; // red line draws after last word (82 + 15*2 + buffer)
const DATE_ENTRANCE = 155;
const TIME_ENTRANCE = 185;
const ADDRESS_ENTRANCE = 215;
const CTA_ENTRANCE = 248;

// ACT 3 — Exits (staggered, CTA first, EAC last)
const CTA_EXIT = 355;
const ADDRESS_EXIT = 365;
const DATETIME_EXIT = 375;
const TITLE_EXIT = 388;
const BG_EXIT = 395; // background shape exits

export const JPOComposition: React.FC = () => {
	return (
		<AbsoluteFill style={{overflow: 'hidden'}}>
			{/* Layer 0 — animated background (always present) */}
			<Background />

			{/* Layer 1 — EAC logo (enters early, stays till very end with glow) */}
			<LogoTitle entranceFrame={EAC_ENTRANCE} />

			{/* Layer 2 — "JOURNÉE PORTES OUVERTES" staggered word reveal + red divider */}
			<EventTitle
				entranceFrame={TITLE_ENTRANCE}
				dividerFrame={DIVIDER_FRAME}
				exitFrame={TITLE_EXIT}
			/>

			{/* Layer 3 — "14 MARS" scale spring + "14H – 16H" fade */}
			<DateBlock
				dateEntranceFrame={DATE_ENTRANCE}
				timeEntranceFrame={TIME_ENTRANCE}
				exitFrame={DATETIME_EXIT}
			/>

			{/* Layer 4 — address blur-to-clear entrance */}
			<AddressBlock entranceFrame={ADDRESS_ENTRANCE} exitFrame={ADDRESS_EXIT} />

			{/* Layer 5 — CTA red pill button with bouncy spring */}
			<CTAButton entranceFrame={CTA_ENTRANCE} exitFrame={CTA_EXIT} />
		</AbsoluteFill>
	);
};

// Re-export timing constants so Root.tsx can reference them if needed
export {BG_ENTRANCE};
