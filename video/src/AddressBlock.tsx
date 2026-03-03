import React from 'react';
import {
	AbsoluteFill,
	interpolate,
	spring,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';

// Animation technique: Subtle fade-in combined with a CSS filter blur transition
// (blur: 6px → 0px) using spring physics for a "focus-in" effect.
// The address sits at 70% opacity for secondary text hierarchy.

const {fontFamily} = loadFont('normal', {
	weights: ['400'],
	subsets: ['latin'],
});

const WHITE = '#FFFFFF';

interface AddressBlockProps {
	entranceFrame: number;
	exitFrame: number;
}

export const AddressBlock: React.FC<AddressBlockProps> = ({
	entranceFrame,
	exitFrame,
}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();

	// Blur-to-clear entrance: opacity + filter blur using spring
	const f = Math.max(0, frame - entranceFrame);
	const s = spring({fps, frame: f, config: {damping: 200, stiffness: 60}});

	const opacity = interpolate(s, [0, 0.5, 1], [0, 0.5, 0.7]);
	const blur = interpolate(s, [0, 1], [8, 0]);
	const translateY = interpolate(s, [0, 1], [14, 0]);

	// ACT 3: fade out
	const outroOpacity = interpolate(frame, [exitFrame, exitFrame + 25], [1, 0], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	return (
		<AbsoluteFill
			style={{
				justifyContent: 'flex-start',
				alignItems: 'center',
				paddingTop: 850,
				pointerEvents: 'none',
			}}
		>
			<div
				style={{
					fontFamily,
					fontSize: 36,
					fontWeight: 400,
					color: WHITE,
					letterSpacing: 2,
					textAlign: 'center',
					opacity: opacity * outroOpacity,
					filter: `blur(${blur}px)`,
					transform: `translateY(${translateY}px)`,
					paddingLeft: 60,
					paddingRight: 60,
					boxSizing: 'border-box',
					width: '100%',
				}}
			>
				13 rue Miollis · 75015 Paris
			</div>
		</AbsoluteFill>
	);
};
