import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

// Animation technique: Large red SVG polygon swept in via translateX+translateY
// using Easing.bezier(0.16, 1, 0.3, 1) for a cinematic ease-out (bottom-left → top-right).
// Geometric white lines fade in alongside the sweep for depth.

const RED = '#DC0D17';
const NAVY = '#1C2459';
const WHITE = '#FFFFFF';

export const Background: React.FC = () => {
	const frame = useCurrentFrame();
	const {width, height} = useVideoConfig();

	// ACT 1: Red diagonal shape sweeps in from bottom-left (frames 0–60)
	const sweepProgress = interpolate(frame, [0, 60], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing: Easing.bezier(0.16, 1, 0.3, 1),
	});

	// ACT 3: Red shape sweeps back out to top-right (frames 395–445)
	const exitProgress = interpolate(frame, [395, 445], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing: Easing.bezier(0.7, 0, 0.84, 0),
	});

	// Diagonal sweep: combine X and Y translation for bottom-left → top-right motion
	const txIn = interpolate(sweepProgress, [0, 1], [-width * 1.3, 0]);
	const tyIn = interpolate(sweepProgress, [0, 1], [height * 0.4, 0]);
	const txOut = interpolate(exitProgress, [0, 1], [0, width * 1.3]);
	const tyOut = interpolate(exitProgress, [0, 1], [0, -height * 0.4]);

	const translateX = txIn + txOut;
	const translateY = tyIn + tyOut;

	// Geometric white lines fade in during ACT 1, fade out during ACT 3
	const linesIn = interpolate(frame, [20, 55], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	const linesOut = interpolate(frame, [380, 420], [1, 0], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	const linesOpacity = Math.min(linesIn, linesOut);

	// Red shape polygon: trapezoid covering lower ~80% of screen with diagonal top edge
	// Top edge goes from (0, h*0.22) on left to (w, h*0.07) on right (upward-right slant)
	const p1x = 0;
	const p1y = height * 0.22;
	const p2x = width;
	const p2y = height * 0.07;
	const p3x = width;
	const p3y = height + 50;
	const p4x = 0;
	const p4y = height + 50;

	const shapePoints = `${p1x},${p1y} ${p2x},${p2y} ${p3x},${p3y} ${p4x},${p4y}`;

	return (
		<AbsoluteFill style={{background: NAVY, overflow: 'hidden'}}>
			{/* Large red diagonal shape — main visual anchor */}
			<svg
				width={width}
				height={height}
				style={{
					position: 'absolute',
					left: 0,
					top: 0,
					transform: `translate(${translateX}px, ${translateY}px)`,
				}}
				viewBox={`0 0 ${width} ${height}`}
			>
				<polygon points={shapePoints} fill={RED} />
			</svg>

			{/* Decorative geometric lines — add depth to the navy area */}
			<svg
				width={width}
				height={height}
				style={{
					position: 'absolute',
					left: 0,
					top: 0,
					opacity: linesOpacity,
				}}
				viewBox={`0 0 ${width} ${height}`}
			>
				{/* Short diagonal accent — top-left */}
				<line
					x1={width * 0.06}
					y1={height * 0.04}
					x2={width * 0.28}
					y2={height * 0.14}
					stroke={WHITE}
					strokeWidth={1.2}
					opacity={0.25}
				/>
				{/* Parallel echo line — top-left */}
				<line
					x1={width * 0.06}
					y1={height * 0.07}
					x2={width * 0.2}
					y2={height * 0.12}
					stroke={WHITE}
					strokeWidth={0.6}
					opacity={0.12}
				/>
				{/* Short diagonal accent — top-right */}
				<line
					x1={width * 0.72}
					y1={height * 0.04}
					x2={width * 0.95}
					y2={height * 0.12}
					stroke={WHITE}
					strokeWidth={1.2}
					opacity={0.25}
				/>
				{/* Vertical tick mark — left */}
				<line
					x1={width * 0.07}
					y1={height * 0.15}
					x2={width * 0.07}
					y2={height * 0.19}
					stroke={WHITE}
					strokeWidth={1.5}
					opacity={0.3}
				/>
				{/* Vertical tick mark — right */}
				<line
					x1={width * 0.93}
					y1={height * 0.15}
					x2={width * 0.93}
					y2={height * 0.19}
					stroke={WHITE}
					strokeWidth={1.5}
					opacity={0.3}
				/>
				{/* Subtle cross-diagonal in navy zone */}
				<line
					x1={0}
					y1={height * 0.02}
					x2={width}
					y2={height * 0.18}
					stroke={WHITE}
					strokeWidth={0.4}
					opacity={0.07}
				/>
			</svg>
		</AbsoluteFill>
	);
};
