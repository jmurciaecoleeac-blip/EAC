import React from 'react';
import {
	AbsoluteFill,
	interpolate,
	Sequence,
	spring,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';

const Title: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();

	const opacity = interpolate(frame, [0, 20], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	const scale = spring({
		fps,
		frame,
		config: {damping: 200},
	});

	return (
		<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
			<div
				style={{
					opacity,
					transform: `scale(${scale})`,
					color: 'white',
					fontSize: 90,
					fontWeight: 'bold',
					fontFamily: 'sans-serif',
					textAlign: 'center',
				}}
			>
				Remotion Skill
			</div>
		</AbsoluteFill>
	);
};

const Subtitle: React.FC = () => {
	const frame = useCurrentFrame();

	const opacity = interpolate(frame, [0, 20], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	const translateY = interpolate(frame, [0, 20], [20, 0], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	return (
		<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', paddingTop: 160}}>
			<div
				style={{
					opacity,
					transform: `translateY(${translateY}px)`,
					color: '#aaaaaa',
					fontSize: 40,
					fontFamily: 'sans-serif',
					textAlign: 'center',
				}}
			>
				Skill installé avec succès ✓
			</div>
		</AbsoluteFill>
	);
};

export const MyComp: React.FC = () => {
	return (
		<AbsoluteFill style={{background: '#0c0c0c'}}>
			<Sequence from={0} durationInFrames={120}>
				<Title />
			</Sequence>
			<Sequence from={30} durationInFrames={90}>
				<Subtitle />
			</Sequence>
		</AbsoluteFill>
	);
};
