import React from 'react';
import {
	AbsoluteFill,
	interpolate,
	spring,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';

const RED = '#DC0D17';
const DARK_RED = '#b00b13';
const NAVY = '#1A1F4E';
const WHITE = '#FFFFFF';

/* ─── Sub-components ─────────────────────────────────────────── */

const DropIn: React.FC<{
	delay: number;
	children: React.ReactNode;
	style?: React.CSSProperties;
}> = ({delay, children, style}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f = Math.max(0, frame - delay);
	const s = spring({fps, frame: f, config: {damping: 160, stiffness: 80}});
	const y = interpolate(s, [0, 1], [-140, 0]);
	const opacity = interpolate(f, [0, 10], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	return (
		<div style={{transform: `translateY(${y}px)`, opacity, ...style}}>
			{children}
		</div>
	);
};

const SlideUp: React.FC<{
	delay: number;
	children: React.ReactNode;
	style?: React.CSSProperties;
}> = ({delay, children, style}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f = Math.max(0, frame - delay);
	const s = spring({fps, frame: f, config: {damping: 200, stiffness: 100}});
	const y = interpolate(s, [0, 1], [80, 0]);
	const opacity = interpolate(f, [0, 8], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	return (
		<div style={{transform: `translateY(${y}px)`, opacity, ...style}}>
			{children}
		</div>
	);
};

const PopIn: React.FC<{
	delay: number;
	children: React.ReactNode;
	style?: React.CSSProperties;
}> = ({delay, children, style}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f = Math.max(0, frame - delay);
	const s = spring({fps, frame: f, config: {damping: 110, stiffness: 220}});
	const opacity = interpolate(f, [0, 6], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	return (
		<div style={{transform: `scale(${s})`, opacity, ...style}}>
			{children}
		</div>
	);
};

const WipeBanner: React.FC<{
	delay: number;
	bgColor: string;
	fromRight?: boolean;
	children: React.ReactNode;
}> = ({delay, bgColor, fromRight = false, children}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f = Math.max(0, frame - delay);
	const s = spring({fps, frame: f, config: {damping: 200, stiffness: 85}});
	return (
		<div
			style={{
				background: bgColor,
				transform: `scaleX(${s})`,
				transformOrigin: fromRight ? 'right center' : 'left center',
				width: '100%',
				overflow: 'hidden',
			}}
		>
			{children}
		</div>
	);
};

/* ─── Main Component ─────────────────────────────────────────── */

export const MyComp: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();

	// Background reveal
	const bgIn = interpolate(frame, [0, 8], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	// Central frame scale-in
	const frameSpring = spring({
		fps,
		frame: Math.max(0, frame - 48),
		config: {damping: 200, stiffness: 65},
	});

	// CTA breathing pulse
	const pulse = Math.sin((frame / fps) * Math.PI * 1.5);
	const ctaPulse = interpolate(pulse, [-1, 1], [0.988, 1.012]);

	// Frame interior stripe animations
	const stripes = [0, 1, 2, 3, 4, 5, 6, 7].map((i) =>
		spring({
			fps,
			frame: Math.max(0, frame - (62 + i * 7)),
			config: {damping: 200, stiffness: 90},
		})
	);

	// Text fade inside frame
	const innerTextOpacity = interpolate(frame, [100, 138], [0, 0.18], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	// Address fade-in
	const addressOpacity = interpolate(frame, [195, 225], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	return (
		<AbsoluteFill
			style={{
				background: RED,
				fontFamily: "'Arial Black', 'Arial Bold', Arial, Helvetica, sans-serif",
				overflow: 'hidden',
				opacity: bgIn,
			}}
		>
			{/* ══════════════════════════════════
			    1. EAC Logo — drops from top
			    ══════════════════════════════════ */}
			<DropIn
				delay={5}
				style={{
					position: 'absolute',
					top: 90,
					left: 0,
					right: 0,
					display: 'flex',
					flexDirection: 'column',
					alignItems: 'center',
					gap: 26,
				}}
			>
				{/* Bordered EAC box */}
				<div
					style={{
						border: `5px solid ${WHITE}`,
						padding: '18px 52px',
					}}
				>
					<div
						style={{
							color: WHITE,
							fontSize: 90,
							fontWeight: 900,
							letterSpacing: 24,
							lineHeight: 1,
							textAlign: 'center',
						}}
					>
						EAC
					</div>
				</div>

				{/* School subtitle */}
				<div
					style={{
						color: WHITE,
						fontSize: 23,
						fontWeight: 400,
						letterSpacing: 1.8,
						textAlign: 'center',
						fontFamily: 'Arial, Helvetica, sans-serif',
						lineHeight: 1.6,
						opacity: 0.92,
					}}
				>
					L'ÉCOLE FRANÇAISE DU MARCHÉ
					<br />
					DE L'ART, DE LA CULTURE ET DU LUXE
				</div>
			</DropIn>

			{/* ══════════════════════════════════
			    2. JOURNÉE PORTES OUVERTES — wipe left
			    ══════════════════════════════════ */}
			<div style={{position: 'absolute', top: 418, left: 0, right: 0}}>
				<WipeBanner delay={26} bgColor={WHITE}>
					<div style={{padding: '26px 32px', textAlign: 'center'}}>
						<div
							style={{
								color: RED,
								fontSize: 56,
								fontWeight: 900,
								textTransform: 'uppercase',
								lineHeight: 1,
								fontStyle: 'italic',
								letterSpacing: 1,
							}}
						>
							JOURNÉE PORTES OUVERTES
						</div>
					</div>
				</WipeBanner>
			</div>

			{/* ══════════════════════════════════
			    3. Central white frame — scales in
			    ══════════════════════════════════ */}
			<div
				style={{
					position: 'absolute',
					top: 528,
					left: 64,
					right: 64,
					height: 836,
					border: `14px solid ${WHITE}`,
					transform: `scale(${interpolate(frameSpring, [0, 1], [0.55, 1])})`,
					opacity: frameSpring,
					overflow: 'hidden',
				}}
			>
				<div
					style={{
						width: '100%',
						height: '100%',
						background: DARK_RED,
						display: 'flex',
						flexDirection: 'column',
						alignItems: 'center',
						justifyContent: 'center',
						gap: 18,
						padding: '60px 50px',
					}}
				>
					{/* Animated horizontal stripes */}
					{stripes.map((sp, i) => (
						<div
							key={i}
							style={{
								height: i === 3 || i === 4 ? 3 : 1,
								background: WHITE,
								opacity: i === 3 || i === 4 ? 0.55 : 0.22,
								width: `${interpolate(sp, [0, 1], [0, 100])}%`,
								alignSelf: i % 2 === 0 ? 'flex-start' : 'flex-end',
							}}
						/>
					))}

					{/* Ghost text inside frame */}
					<div
						style={{
							color: WHITE,
							fontSize: 110,
							fontWeight: 900,
							letterSpacing: 14,
							opacity: innerTextOpacity,
							marginTop: 28,
							textAlign: 'center',
						}}
					>
						JPO
					</div>

					{/* More stripes below */}
					{[8, 9, 10].map((i) => {
						const sp2 = spring({
							fps,
							frame: Math.max(0, frame - (62 + i * 7)),
							config: {damping: 200, stiffness: 90},
						});
						return (
							<div
								key={i}
								style={{
									height: 1,
									background: WHITE,
									opacity: 0.18,
									width: `${interpolate(sp2, [0, 1], [0, 100])}%`,
									alignSelf: i % 2 === 0 ? 'flex-start' : 'flex-end',
								}}
							/>
						);
					})}
				</div>
			</div>

			{/* ══════════════════════════════════
			    4. Date badge — pops in (navy pill)
			    ══════════════════════════════════ */}
			<div
				style={{
					position: 'absolute',
					top: 1376,
					left: 0,
					right: 0,
					display: 'flex',
					justifyContent: 'center',
				}}
			>
				<PopIn delay={116}>
					<div
						style={{
							background: NAVY,
							paddingTop: 22,
							paddingBottom: 22,
							paddingLeft: 58,
							paddingRight: 58,
						}}
					>
						<div
							style={{
								color: WHITE,
								fontSize: 44,
								fontWeight: 900,
								letterSpacing: 2,
								textTransform: 'uppercase',
								whiteSpace: 'nowrap',
							}}
						>
							PARIS · 14 MARS · 10H–16H
						</div>
					</div>
				</PopIn>
			</div>

			{/* ══════════════════════════════════
			    5. MARCHÉ banner — wipes right
			    ══════════════════════════════════ */}
			<div style={{position: 'absolute', top: 1498, left: 0, right: 0}}>
				<WipeBanner delay={142} bgColor={WHITE} fromRight>
					<div style={{padding: '24px 32px', textAlign: 'center'}}>
						<div
							style={{
								color: RED,
								fontSize: 44,
								fontWeight: 900,
								textTransform: 'uppercase',
								lineHeight: 1,
								fontStyle: 'italic',
								letterSpacing: 1,
							}}
						>
							MARCHÉ DE L'ART · CULTURE · LUXE
						</div>
					</div>
				</WipeBanner>
			</div>

			{/* ══════════════════════════════════
			    6. RÉSERVE TA PLACE ! — slides up
			    ══════════════════════════════════ */}
			<div
				style={{
					position: 'absolute',
					top: 1612,
					left: 0,
					right: 0,
					display: 'flex',
					justifyContent: 'center',
				}}
			>
				<SlideUp delay={166}>
					<div style={{transform: `scale(${ctaPulse})`}}>
						<div
							style={{
								background: WHITE,
								paddingTop: 28,
								paddingBottom: 28,
								paddingLeft: 80,
								paddingRight: 80,
								textAlign: 'center',
							}}
						>
							<div
								style={{
									color: NAVY,
									fontSize: 56,
									fontWeight: 900,
									letterSpacing: 2,
									textTransform: 'uppercase',
								}}
							>
								RÉSERVE TA PLACE !
							</div>
						</div>
					</div>
				</SlideUp>
			</div>

			{/* ══════════════════════════════════
			    7. Address — fades in
			    ══════════════════════════════════ */}
			<div
				style={{
					position: 'absolute',
					bottom: 80,
					left: 0,
					right: 0,
					textAlign: 'center',
					opacity: addressOpacity,
				}}
			>
				<div
					style={{
						color: WHITE,
						fontSize: 26,
						fontWeight: 400,
						letterSpacing: 3,
						fontFamily: 'Arial, Helvetica, sans-serif',
						opacity: 0.75,
						textTransform: 'uppercase',
					}}
				>
					13 rue Miollis · 75015 Paris
				</div>
			</div>
		</AbsoluteFill>
	);
};
