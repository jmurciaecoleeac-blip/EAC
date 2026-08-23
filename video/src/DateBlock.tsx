import React from 'react';
import {
	AbsoluteFill,
	interpolate,
	spring,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import {FONT_FAMILY} from './fonts';

// Animation technique: "14 MARS" uses a bold scale spring (0.8 → 1) with opacity.
// "14H – 16H" uses a gentle fade + slide-up for secondary info hierarchy.

const fontFamilyBold = FONT_FAMILY;
const fontFamilyRegular = FONT_FAMILY;

const WHITE = '#FFFFFF';
const RED = '#DC0D17';

interface DateBlockProps {
	dateEntranceFrame: number;
	timeEntranceFrame: number;
	exitFrame: number;
}

export const DateBlock: React.FC<DateBlockProps> = ({
	dateEntranceFrame,
	timeEntranceFrame,
	exitFrame,
}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();

	// "14 MARS" — scale spring from 0.8 to 1
	const dateF = Math.max(0, frame - dateEntranceFrame);
	const dateSpring = spring({
		fps,
		frame: dateF,
		config: {damping: 200, stiffness: 100, mass: 0.8},
	});
	const dateScale = interpolate(dateSpring, [0, 1], [0.8, 1]);
	const dateOpacity = interpolate(dateSpring, [0, 0.25, 1], [0, 1, 1]);

	// "14H – 16H" — fade-in with slide-up
	const timeF = Math.max(0, frame - timeEntranceFrame);
	const timeSpring = spring({
		fps,
		frame: timeF,
		config: {damping: 200, stiffness: 80},
	});
	const timeY = interpolate(timeSpring, [0, 1], [20, 0]);
	const timeOpacity = interpolate(timeSpring, [0, 0.4, 1], [0, 0.8, 1]);

	// ACT 3 outro: whole block fades up and out
	const outroOpacity = interpolate(frame, [exitFrame, exitFrame + 30], [1, 0], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	const outroY = interpolate(frame, [exitFrame, exitFrame + 30], [0, -25], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	return (
		<AbsoluteFill
			style={{
				justifyContent: 'flex-start',
				alignItems: 'center',
				paddingTop: 560,
				pointerEvents: 'none',
			}}
		>
			<div
				style={{
					opacity: outroOpacity,
					transform: `translateY(${outroY}px)`,
					textAlign: 'center',
					width: '100%',
				}}
			>
				{/* "14 MARS" — hero date */}
				<div
					style={{
						fontFamily: fontFamilyBold,
						fontSize: 130,
						fontWeight: 900,
						color: WHITE,
						lineHeight: 1,
						letterSpacing: 4,
						transform: `scale(${dateScale})`,
						opacity: dateOpacity,
						textAlign: 'center',
					}}
				>
					14 MARS
				</div>

				{/* "14H – 16H" — event time in red */}
				<div
					style={{
						fontFamily: fontFamilyRegular,
						fontSize: 48,
						fontWeight: 400,
						color: RED,
						letterSpacing: 6,
						marginTop: 16,
						transform: `translateY(${timeY}px)`,
						opacity: timeOpacity,
						textAlign: 'center',
					}}
				>
					14H – 16H
				</div>
			</div>
		</AbsoluteFill>
	);
};
