import React from 'react';
import {
	AbsoluteFill,
	interpolate,
	spring,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import {FONT_FAMILY as fontFamily} from './fonts';

// Animation technique: Staggered word-by-word clip reveal — each word slides up
// from within an overflow:hidden container, creating a "card reveal" effect.
// 15-frame delay between each word. scaleX interpolation draws the red divider.

const WHITE = '#FFFFFF';
const RED = '#DC0D17';
const WORDS = ['JOURNÉE', 'PORTES', 'OUVERTES'];
const WORD_DELAY = 15; // frames between each word

interface WordRevealProps {
	word: string;
	startFrame: number;
}

const WordReveal: React.FC<WordRevealProps> = ({word, startFrame}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f = Math.max(0, frame - startFrame);
	const s = spring({fps, frame: f, config: {damping: 180, stiffness: 80}});
	const translateY = interpolate(s, [0, 1], [100, 0]);
	const opacity = interpolate(s, [0, 0.2, 1], [0, 1, 1]);

	return (
		<div style={{overflow: 'hidden', lineHeight: 1.1}}>
			<div style={{transform: `translateY(${translateY}%)`, opacity}}>
				{word}
			</div>
		</div>
	);
};

interface DividerProps {
	startFrame: number;
	exitFrame: number;
}

const Divider: React.FC<DividerProps> = ({startFrame, exitFrame}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f = Math.max(0, frame - startFrame);
	const scaleX = spring({fps, frame: f, config: {damping: 200, stiffness: 60}});

	const exitOpacity = interpolate(frame, [exitFrame, exitFrame + 25], [1, 0], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	return (
		<div
			style={{
				height: 3,
				background: RED,
				transformOrigin: 'left center',
				transform: `scaleX(${scaleX})`,
				marginTop: 22,
				marginBottom: 0,
				width: '100%',
				opacity: exitOpacity,
			}}
		/>
	);
};

interface EventTitleProps {
	entranceFrame: number;
	dividerFrame: number;
	exitFrame: number;
}

export const EventTitle: React.FC<EventTitleProps> = ({
	entranceFrame,
	dividerFrame,
	exitFrame,
}) => {
	const frame = useCurrentFrame();

	// Fade out entire block during outro
	const outroOpacity = interpolate(frame, [exitFrame, exitFrame + 30], [1, 0], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	const outroY = interpolate(frame, [exitFrame, exitFrame + 30], [0, -20], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	return (
		<AbsoluteFill
			style={{
				justifyContent: 'flex-start',
				alignItems: 'center',
				paddingTop: 410,
				pointerEvents: 'none',
			}}
		>
			<div
				style={{
					opacity: outroOpacity,
					transform: `translateY(${outroY}px)`,
					width: '100%',
					paddingLeft: 60,
					paddingRight: 60,
					boxSizing: 'border-box',
				}}
			>
				{/* Staggered word reveal */}
				<div
					style={{
						fontFamily,
						fontSize: 52,
						fontWeight: 700,
						color: WHITE,
						letterSpacing: 4,
						textAlign: 'center',
						textTransform: 'uppercase',
						display: 'flex',
						flexDirection: 'row',
						justifyContent: 'center',
						gap: 14,
						flexWrap: 'wrap',
					}}
				>
					{WORDS.map((word, i) => (
						<WordReveal
							key={word}
							word={word}
							startFrame={entranceFrame + i * WORD_DELAY}
						/>
					))}
				</div>

				{/* Red horizontal divider draws from left to right */}
				<Divider startFrame={dividerFrame} exitFrame={exitFrame} />
			</div>
		</AbsoluteFill>
	);
};
