import React from 'react';
import {
	AbsoluteFill,
	interpolate,
	spring,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';

const RED = '#DC0D17';
const NAVY = '#1C2459';
const WHITE = '#FFFFFF';
const LIGHT_BLUE = '#8892b8';

/* ─── Sub-components ─────────────────────────────────────────── */

const SlideUp: React.FC<{
	delay: number;
	children: React.ReactNode;
	style?: React.CSSProperties;
}> = ({delay, children, style}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f = Math.max(0, frame - delay);
	const s = spring({fps, frame: f, config: {damping: 200, stiffness: 120}});
	const y = interpolate(s, [0, 1], [90, 0]);
	const opacity = interpolate(f, [0, 14], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	return (
		<div style={{transform: `translateY(${y}px)`, opacity, ...style}}>
			{children}
		</div>
	);
};

const SlideLeft: React.FC<{
	delay: number;
	children: React.ReactNode;
	style?: React.CSSProperties;
}> = ({delay, children, style}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f = Math.max(0, frame - delay);
	const s = spring({fps, frame: f, config: {damping: 200, stiffness: 120}});
	const x = interpolate(s, [0, 1], [-90, 0]);
	const opacity = interpolate(f, [0, 14], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	return (
		<div style={{transform: `translateX(${x}px)`, opacity, ...style}}>
			{children}
		</div>
	);
};

const ScaleIn: React.FC<{
	delay: number;
	children: React.ReactNode;
	style?: React.CSSProperties;
}> = ({delay, children, style}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f = Math.max(0, frame - delay);
	const s = spring({fps, frame: f, config: {damping: 200, stiffness: 90}});
	const scale = interpolate(s, [0, 1], [0.2, 1]);
	const opacity = interpolate(f, [0, 16], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	return (
		<div
			style={{
				transform: `scale(${scale})`,
				opacity,
				transformOrigin: 'left bottom',
				...style,
			}}
		>
			{children}
		</div>
	);
};

const LineReveal: React.FC<{
	delay: number;
	color: string;
	thickness?: number;
}> = ({delay, color, thickness = 4}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f = Math.max(0, frame - delay);
	const s = spring({fps, frame: f, config: {damping: 200, stiffness: 70}});
	const width = interpolate(s, [0, 1], [0, 100]);
	return (
		<div
			style={{
				height: thickness,
				width: `${width}%`,
				background: color,
			}}
		/>
	);
};

/* ─── Main Component ─────────────────────────────────────────── */

export const MyComp: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();

	// Background geometric shapes
	const circle1 = spring({
		fps,
		frame: Math.max(0, frame - 3),
		config: {damping: 200, stiffness: 60},
	});
	const circle2 = spring({
		fps,
		frame: Math.max(0, frame - 12),
		config: {damping: 200, stiffness: 50},
	});
	const diagonalProgress = spring({
		fps,
		frame: Math.max(0, frame - 5),
		config: {damping: 200, stiffness: 60},
	});

	// Pulsing dot animation
	const pulseValue = Math.sin((frame / fps) * Math.PI * 2.5);
	const pulseOpacity = interpolate(pulseValue, [-1, 1], [0.5, 1]);

	// Global fade-in
	const globalOpacity = interpolate(frame, [0, 15], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	return (
		<AbsoluteFill
			style={{
				background: NAVY,
				fontFamily: "'Arial Black', 'Arial Bold', Arial, Helvetica, sans-serif",
				overflow: 'hidden',
				opacity: globalOpacity,
			}}
		>
			{/* ── Decorative background shapes ── */}
			<AbsoluteFill>
				{/* Large red circle – top right */}
				<div
					style={{
						position: 'absolute',
						top: -280,
						right: -320,
						width: 800,
						height: 800,
						borderRadius: '50%',
						background: RED,
						opacity: 0.13,
						transform: `scale(${interpolate(circle1, [0, 1], [0.1, 1])})`,
					}}
				/>
				{/* Circle outline – bottom left */}
				<div
					style={{
						position: 'absolute',
						bottom: -200,
						left: -220,
						width: 700,
						height: 700,
						borderRadius: '50%',
						border: `4px solid ${RED}`,
						opacity: 0.18,
						transform: `scale(${interpolate(circle2, [0, 1], [0.1, 1])})`,
					}}
				/>
				{/* Inner circle outline */}
				<div
					style={{
						position: 'absolute',
						bottom: -90,
						left: -100,
						width: 420,
						height: 420,
						borderRadius: '50%',
						border: `2px solid ${WHITE}`,
						opacity: 0.07,
						transform: `scale(${interpolate(circle2, [0, 1], [0.1, 1])})`,
					}}
				/>
				{/* Diagonal gradient band */}
				<div
					style={{
						position: 'absolute',
						top: 0,
						left: 0,
						width: '100%',
						height: '100%',
						background: `linear-gradient(140deg, ${RED} 0%, transparent 40%)`,
						opacity: interpolate(diagonalProgress, [0, 1], [0, 0.10]),
					}}
				/>
				{/* Thin diagonal stripe */}
				<div
					style={{
						position: 'absolute',
						top: 320,
						left: -60,
						width: 8,
						height: `${interpolate(diagonalProgress, [0, 1], [0, 180])}%`,
						background: RED,
						opacity: 0.25,
						transform: 'rotate(20deg)',
						transformOrigin: 'top center',
					}}
				/>
			</AbsoluteFill>

			{/* ── TOP SECTION: EAC brand ── */}
			<AbsoluteFill
				style={{
					padding: '100px 80px 0',
					flexDirection: 'column',
					justifyContent: 'flex-start',
					alignItems: 'flex-start',
				}}
			>
				{/* Top red accent line */}
				<LineReveal delay={5} color={RED} thickness={6} />

				{/* EAC */}
				<div style={{marginTop: 32}}>
					<SlideLeft delay={18}>
						<div
							style={{
								color: WHITE,
								fontSize: 68,
								fontWeight: 900,
								letterSpacing: 18,
								textTransform: 'uppercase',
								lineHeight: 1,
							}}
						>
							EAC
						</div>
					</SlideLeft>
					<SlideLeft delay={30}>
						<div
							style={{
								color: LIGHT_BLUE,
								fontSize: 23,
								fontWeight: 400,
								letterSpacing: 1.5,
								marginTop: 8,
								fontFamily: 'Arial, Helvetica, sans-serif',
							}}
						>
							École des Arts et Communication
						</div>
					</SlideLeft>
				</div>
			</AbsoluteFill>

			{/* ── CENTER: Main title + date ── */}
			<AbsoluteFill
				style={{
					padding: '0 80px',
					flexDirection: 'column',
					justifyContent: 'center',
					alignItems: 'flex-start',
				}}
			>
				{/* Label */}
				<SlideLeft delay={55}>
					<div
						style={{
							color: RED,
							fontSize: 19,
							fontWeight: 700,
							letterSpacing: 8,
							textTransform: 'uppercase',
							marginBottom: 28,
							fontFamily: 'Arial, Helvetica, sans-serif',
						}}
					>
						· Invitation ·
					</div>
				</SlideLeft>

				{/* JOURNÉE */}
				<div style={{overflow: 'hidden'}}>
					<SlideUp delay={65}>
						<div
							style={{
								color: WHITE,
								fontSize: 104,
								fontWeight: 900,
								lineHeight: 1.05,
								textTransform: 'uppercase',
							}}
						>
							Journée
						</div>
					</SlideUp>
				</div>

				{/* PORTES */}
				<div style={{overflow: 'hidden'}}>
					<SlideUp delay={80}>
						<div
							style={{
								color: WHITE,
								fontSize: 104,
								fontWeight: 900,
								lineHeight: 1.05,
								textTransform: 'uppercase',
							}}
						>
							Portes
						</div>
					</SlideUp>
				</div>

				{/* OUVERTES – red */}
				<div style={{overflow: 'hidden'}}>
					<SlideUp delay={96}>
						<div
							style={{
								color: RED,
								fontSize: 104,
								fontWeight: 900,
								lineHeight: 1.05,
								textTransform: 'uppercase',
							}}
						>
							Ouvertes
						</div>
					</SlideUp>
				</div>

				{/* Separator */}
				<div style={{marginTop: 44, marginBottom: 44, width: '100%'}}>
					<LineReveal delay={116} color={WHITE} thickness={2} />
				</div>

				{/* DATE: 14 + MARS */}
				<div
					style={{
						display: 'flex',
						alignItems: 'flex-end',
						gap: 24,
					}}
				>
					<div style={{overflow: 'hidden'}}>
						<ScaleIn delay={126}>
							<div
								style={{
									color: WHITE,
									fontSize: 160,
									fontWeight: 900,
									lineHeight: 0.9,
								}}
							>
								14
							</div>
						</ScaleIn>
					</div>

					<div style={{paddingBottom: 18}}>
						<div style={{overflow: 'hidden'}}>
							<SlideUp delay={142}>
								<div
									style={{
										color: RED,
										fontSize: 70,
										fontWeight: 900,
										textTransform: 'uppercase',
										letterSpacing: 8,
										lineHeight: 1,
									}}
								>
									Mars
								</div>
							</SlideUp>
						</div>
					</div>
				</div>

				{/* TIME */}
				<SlideLeft delay={158}>
					<div
						style={{
							color: WHITE,
							fontSize: 42,
							fontWeight: 500,
							letterSpacing: 5,
							marginTop: 20,
							opacity: 0.88,
							fontFamily: 'Arial, Helvetica, sans-serif',
						}}
					>
						10H — 16H
					</div>
				</SlideLeft>
			</AbsoluteFill>

			{/* ── BOTTOM: Address ── */}
			<AbsoluteFill
				style={{
					padding: '0 80px 110px',
					flexDirection: 'column',
					justifyContent: 'flex-end',
					alignItems: 'flex-start',
				}}
			>
				<LineReveal delay={182} color={RED} thickness={3} />

				<div style={{marginTop: 26}}>
					<div style={{overflow: 'hidden'}}>
						<SlideUp delay={192}>
							<div
								style={{
									color: WHITE,
									fontSize: 34,
									fontWeight: 700,
									letterSpacing: 1,
									fontFamily: 'Arial, Helvetica, sans-serif',
								}}
							>
								13 rue Miollis
							</div>
						</SlideUp>
					</div>

					<div style={{overflow: 'hidden'}}>
						<SlideUp delay={204}>
							<div
								style={{
									color: LIGHT_BLUE,
									fontSize: 30,
									fontWeight: 400,
									marginTop: 6,
									fontFamily: 'Arial, Helvetica, sans-serif',
								}}
							>
								75015 Paris
							</div>
						</SlideUp>
					</div>
				</div>

				{/* Decorative dots */}
				<div
					style={{
						marginTop: 36,
						display: 'flex',
						gap: 12,
						opacity: interpolate(frame, [218, 248], [0, 1], {
							extrapolateLeft: 'clamp',
							extrapolateRight: 'clamp',
						}),
					}}
				>
					{[0, 1, 2].map((i) => (
						<div
							key={i}
							style={{
								width: 10,
								height: 10,
								borderRadius: '50%',
								background: i === 1 ? RED : WHITE,
								opacity: i === 1 ? pulseOpacity : 0.35,
							}}
						/>
					))}
				</div>
			</AbsoluteFill>

			{/* Bottom red accent line */}
			<AbsoluteFill
				style={{
					padding: '0 80px 68px',
					flexDirection: 'column',
					justifyContent: 'flex-end',
				}}
			>
				<div
					style={{
						opacity: interpolate(frame, [205, 235], [0, 1], {
							extrapolateLeft: 'clamp',
							extrapolateRight: 'clamp',
						}),
					}}
				>
					<LineReveal delay={205} color={RED} thickness={6} />
				</div>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
