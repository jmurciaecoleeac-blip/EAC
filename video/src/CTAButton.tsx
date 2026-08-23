import React from 'react';
import {
	AbsoluteFill,
	interpolate,
	spring,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import {FONT_FAMILY as fontFamily} from './fonts';

// Animation technique: Red pill button bounces in using spring with low damping
// (damping: 8) for playful overshoot. A very subtle continuous scale pulse
// (driven by sin of frame) keeps it alive during the content phase.


const RED = '#DC0D17';
const WHITE = '#FFFFFF';

interface CTAButtonProps {
	entranceFrame: number;
	exitFrame: number;
}

export const CTAButton: React.FC<CTAButtonProps> = ({
	entranceFrame,
	exitFrame,
}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();

	// Bouncy spring entrance
	const f = Math.max(0, frame - entranceFrame);
	const s = spring({
		fps,
		frame: f,
		config: {damping: 8, stiffness: 200, mass: 0.6},
	});
	const scaleIn = interpolate(s, [0, 1], [0, 1]);
	const opacity = interpolate(s, [0, 0.15, 1], [0, 1, 1]);

	// Subtle continuous pulse (deterministic: uses frame, not time)
	// Maps frame to a sine wave using integer arithmetic
	// sin approximation: uses frame counter cycling every 60 frames
	const cyclePos = (frame % 90) / 90; // 0 to 1 over 3-second cycle
	// Triangle wave approximation (deterministic, no Math.random)
	const triangle =
		cyclePos < 0.5 ? cyclePos * 2 : 2 - cyclePos * 2; // 0→1→0 over cycle
	const pulse = interpolate(triangle, [0, 1], [0.98, 1.02]);

	// ACT 3: fade out
	const outroOpacity = interpolate(frame, [exitFrame, exitFrame + 25], [1, 0], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	const outroScale = interpolate(frame, [exitFrame, exitFrame + 25], [1, 0.85], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	const finalScale = scaleIn * (f > 30 ? pulse : 1) * outroScale;

	return (
		<AbsoluteFill
			style={{
				justifyContent: 'flex-end',
				alignItems: 'center',
				paddingBottom: 160,
				pointerEvents: 'none',
			}}
		>
			<div
				style={{
					transform: `scale(${finalScale})`,
					opacity: opacity * outroOpacity,
					width: '100%',
					paddingLeft: 70,
					paddingRight: 70,
					boxSizing: 'border-box',
					textAlign: 'center',
				}}
			>
				{/* Red pill/capsule button */}
				<div
					style={{
						background: WHITE,
						borderRadius: 60,
						paddingTop: 28,
						paddingBottom: 28,
						paddingLeft: 40,
						paddingRight: 40,
						display: 'inline-block',
						boxShadow: '0 8px 40px rgba(220, 13, 23, 0.5)',
					}}
				>
					<span
						style={{
							fontFamily,
							fontSize: 38,
							fontWeight: 700,
							color: RED,
							letterSpacing: 1,
							textTransform: 'uppercase',
							whiteSpace: 'nowrap',
						}}
					>
						Inscris-toi maintenant
					</span>
				</div>
			</div>
		</AbsoluteFill>
	);
};
