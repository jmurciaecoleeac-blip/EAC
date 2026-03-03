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
		<div
			style={{
				opacity,
				transform: `scale(${scale})`,
				color: 'white',
				fontSize: 80,
				fontWeight: 'bold',
				fontFamily: 'sans-serif',
				textAlign: 'center',
			}}
		>
			Remotion Skill
		</div>
	);
};

const Subtitle: React.FC = () => {
	const frame = useCurrentFrame();

	const opacity = interpolate(frame, [0, 20], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	return (
		<div
			style={{
				opacity,
				color: '#aaa',
				fontSize: 36,
				fontFamily: 'sans-serif',
				textAlign: 'center',
				marginTop: 20,
			}}
		>
			Skill installé avec succès ✓
		</div>
	);
};

export const MyComp: React.FC = () => {
	return (
		<AbsoluteFill style={{background: '#0c0c0c', justifyContent: 'center', alignItems: 'center', flexDirection: 'column'}}>
			<Sequence from={0} durationInFrames={120}>
				<Title />
			</Sequence>
			<Sequence from={30} durationInFrames={90}>
				<Subtitle />
			</Sequence>
		</AbsoluteFill>
	);
};
