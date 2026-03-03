import React from 'react';
import {Composition} from 'remotion';
import {JPOComposition} from './Composition';
import {JPOLogoMorphComp} from './JPOLogoMorphComp';

// Root registers all compositions.
// Specs: 1080×1920 (Instagram/TikTok Reels vertical), 30 fps, 15 s = 450 frames.
export const Root: React.FC = () => {
	return (
		<>
			<Composition
				id="JPOVideo"
				component={JPOComposition}
				durationInFrames={450}
				width={1080}
				height={1920}
				fps={30}
				defaultProps={{}}
			/>
			<Composition
				id="JPOLogoMorph"
				component={JPOLogoMorphComp}
				durationInFrames={450}
				width={1080}
				height={1920}
				fps={30}
				defaultProps={{}}
			/>
		</>
	);
};
