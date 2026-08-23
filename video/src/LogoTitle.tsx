import React from 'react';
import {
	AbsoluteFill,
	interpolate,
	spring,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import {FONT_FAMILY as fontFamily} from './fonts';

// Animation technique: Bold scale + opacity spring for a punchy entrance.
// ACT 3 outro: EAC remains centered with a subtle glow pulse, fading to 1 last beat.

const WHITE = '#FFFFFF';
const RED = '#DC0D17';

interface LogoTitleProps {
	entranceFrame: number;
}

export const LogoTitle: React.FC<LogoTitleProps> = ({entranceFrame}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();

	// Spring entrance: scale from 0.6 → 1, opacity from 0 → 1
	const f = Math.max(0, frame - entranceFrame);
	const s = spring({
		fps,
		frame: f,
		config: {damping: 12, stiffness: 200, mass: 0.5},
	});
	const scale = interpolate(s, [0, 1], [0.6, 1]);
	const opacity = interpolate(s, [0, 0.3, 1], [0, 0.8, 1]);

	// ACT 3 outro (frames 410–449): EAC stays but fades to a strong glow
	const outroOpacity = interpolate(frame, [410, 445], [1, 0.92], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	// Glow pulse intensifies in outro (frames 410–449)
	const glowRadius = interpolate(frame, [410, 449], [0, 40], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	const glowOpacity = interpolate(frame, [410, 449], [0, 0.6], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	const letterSpacing = interpolate(s, [0, 1], [30, 12]);

	return (
		<AbsoluteFill
			style={{
				justifyContent: 'flex-start',
				alignItems: 'center',
				paddingTop: 148,
				pointerEvents: 'none',
			}}
		>
			<div
				style={{
					fontFamily,
					fontSize: 180,
					fontWeight: 900,
					color: WHITE,
					letterSpacing,
					lineHeight: 1,
					textAlign: 'center',
					transform: `scale(${scale})`,
					opacity: opacity * outroOpacity,
					textShadow:
						glowOpacity > 0
							? `0 0 ${glowRadius}px rgba(255,255,255,${glowOpacity}), 0 0 ${glowRadius * 2}px rgba(${RED},${glowOpacity * 0.5})`
							: 'none',
				}}
			>
				EAC
			</div>
		</AbsoluteFill>
	);
};
