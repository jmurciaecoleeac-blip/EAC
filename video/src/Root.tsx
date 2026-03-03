import React from 'react';
import {Composition} from 'remotion';
import {MyComp} from './MyComp';

export const Root: React.FC = () => {
	return (
		<>
			<Composition
				id="MyComp"
				component={MyComp}
				durationInFrames={300}
				width={1080}
				height={1920}
				fps={30}
				defaultProps={{}}
			/>
		</>
	);
};
