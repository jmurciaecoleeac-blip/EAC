import React from 'react';
import {
	AbsoluteFill,
	interpolate,
	spring,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';

const RED = '#DC0D17';
const NAVY = '#1A1F4E';
const WHITE = '#FFFFFF';

/* ─────────────────────────────────────────────────────────────
   ClipReveal — signature technique des vidéos de mode/luxe.
   Le texte monte depuis le bas d'un overflow:hidden.
   ───────────────────────────────────────────────────────────── */
const ClipReveal: React.FC<{
	delay: number;
	stiffness?: number;
	damping?: number;
	children: React.ReactNode;
}> = ({delay, stiffness = 78, damping = 218, children}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f = Math.max(0, frame - delay);
	const s = spring({fps, frame: f, config: {damping, stiffness}});
	const y = interpolate(s, [0, 1], [110, 0]);
	return (
		<div style={{overflow: 'hidden'}}>
			<div style={{transform: `translateY(${y}%)`}}>{children}</div>
		</div>
	);
};

/* ─────────────────────────────────────────────────────────────
   FadeSlide — opacité + léger glissement vertical.
   Pour les éléments secondaires et les sous-titres.
   ───────────────────────────────────────────────────────────── */
const FadeSlide: React.FC<{
	delay: number;
	fromY?: number;
	targetOpacity?: number;
	children: React.ReactNode;
	style?: React.CSSProperties;
}> = ({delay, fromY = 18, targetOpacity = 1, children, style}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f = Math.max(0, frame - delay);
	const s = spring({fps, frame: f, config: {damping: 200, stiffness: 58}});
	const y = interpolate(s, [0, 1], [fromY, 0]);
	const opacity = interpolate(s, [0, 0.3, 1], [0, targetOpacity * 0.65, targetOpacity]);
	return (
		<div style={{transform: `translateY(${y}px)`, opacity, ...style}}>
			{children}
		</div>
	);
};

/* ─────────────────────────────────────────────────────────────
   LineDraw — fine ligne qui se déploie d'un côté à l'autre.
   ───────────────────────────────────────────────────────────── */
const LineDraw: React.FC<{
	delay: number;
	fromRight?: boolean;
	lineOpacity?: number;
	style?: React.CSSProperties;
}> = ({delay, fromRight = false, lineOpacity = 0.25, style}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f = Math.max(0, frame - delay);
	const s = spring({fps, frame: f, config: {damping: 200, stiffness: 50}});
	return (
		<div
			style={{
				height: 1,
				background: WHITE,
				opacity: lineOpacity,
				transform: `scaleX(${s})`,
				transformOrigin: fromRight ? 'right center' : 'left center',
				...style,
			}}
		/>
	);
};

/* ─────────────────────────────────────────────────────────────
   PanelReveal — panneau blanc qui apparaît en fondu.
   Le contenu texte se révèle ensuite par ClipReveal.
   ───────────────────────────────────────────────────────────── */
const PanelReveal: React.FC<{
	delay: number;
	children: React.ReactNode;
	style?: React.CSSProperties;
}> = ({delay, children, style}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const f = Math.max(0, frame - delay);
	const s = spring({fps, frame: f, config: {damping: 200, stiffness: 76}});
	return <div style={{opacity: s, ...style}}>{children}</div>;
};

/* ─────────────────────────────────────────────────────────────
   COMPOSANT PRINCIPAL
   ───────────────────────────────────────────────────────────── */
export const MyComp: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();

	// Fondu d'entrée global
	const bgIn = interpolate(frame, [0, 10], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	// Respiration subtile sur le CTA
	const ctaPulse = interpolate(
		Math.sin((frame / fps) * Math.PI * 0.85),
		[-1, 1],
		[0.994, 1.006]
	);

	return (
		<AbsoluteFill
			style={{
				background: RED,
				fontFamily: "'Arial Black', 'Arial Bold', Arial, Helvetica, sans-serif",
				overflow: 'hidden',
				opacity: bgIn,
			}}
		>
			{/* ══════════════════════════════
			    1. LIGNE D'ACCENT HAUTE
			    ══════════════════════════════ */}
			<LineDraw
				delay={5}
				lineOpacity={0.20}
				style={{position: 'absolute', top: 74, left: 56, right: 56}}
			/>

			{/* ══════════════════════════════
			    2. SOUS-TITRE ÉCOLE
			    ══════════════════════════════ */}
			<FadeSlide
				delay={10}
				fromY={14}
				targetOpacity={0.75}
				style={{
					position: 'absolute',
					top: 102,
					left: 0,
					right: 0,
					textAlign: 'center',
					color: WHITE,
					fontSize: 20,
					fontWeight: 400,
					fontFamily: 'Arial, Helvetica, sans-serif',
					letterSpacing: 2.5,
					lineHeight: 1.8,
					textTransform: 'uppercase',
				}}
			>
				L'École Française du Marché de l'Art,
				<br />
				de la Culture et du Luxe
			</FadeSlide>

			{/* ══════════════════════════════
			    3. LIGNE D'ACCENT BASSE (inversée)
			    ══════════════════════════════ */}
			<LineDraw
				delay={22}
				fromRight
				lineOpacity={0.16}
				style={{position: 'absolute', top: 210, left: 56, right: 56}}
			/>

			{/* ══════════════════════════════
			    4. PANNEAU "JOURNÉE PORTES OUVERTES"
			    Panneau blanc → texte en clip-reveal (3 lignes)
			    ══════════════════════════════ */}
			<PanelReveal
				delay={26}
				style={{
					position: 'absolute',
					top: 248,
					left: 0,
					right: 0,
					background: WHITE,
					paddingTop: 54,
					paddingBottom: 54,
					paddingLeft: 50,
					paddingRight: 50,
				}}
			>
				<ClipReveal delay={30} stiffness={76} damping={228}>
					<div
						style={{
							color: RED,
							fontSize: 128,
							fontWeight: 900,
							lineHeight: 0.87,
							textTransform: 'uppercase',
							letterSpacing: -3,
						}}
					>
						JOURNÉE
					</div>
				</ClipReveal>

				<ClipReveal delay={43} stiffness={76} damping={228}>
					<div
						style={{
							color: RED,
							fontSize: 128,
							fontWeight: 900,
							lineHeight: 0.92,
							textTransform: 'uppercase',
							letterSpacing: -3,
						}}
					>
						PORTES
					</div>
				</ClipReveal>

				<ClipReveal delay={56} stiffness={76} damping={228}>
					<div
						style={{
							color: RED,
							fontSize: 128,
							fontWeight: 900,
							lineHeight: 0.92,
							textTransform: 'uppercase',
							letterSpacing: -3,
						}}
					>
						OUVERTES
					</div>
				</ClipReveal>
			</PanelReveal>

			{/* ══════════════════════════════
			    5. VILLE — PARIS
			    ══════════════════════════════ */}
			<FadeSlide
				delay={70}
				fromY={12}
				targetOpacity={0.68}
				style={{
					position: 'absolute',
					top: 758,
					left: 0,
					right: 0,
					textAlign: 'center',
					color: WHITE,
					fontSize: 26,
					fontWeight: 400,
					fontFamily: 'Arial, Helvetica, sans-serif',
					letterSpacing: 11,
					textTransform: 'uppercase',
				}}
			>
				Paris
			</FadeSlide>

			{/* ══════════════════════════════
			    6. CHIFFRE HÉRO — "14"
			    Grand, fort, clip-reveal
			    ══════════════════════════════ */}
			<div style={{position: 'absolute', top: 797, left: 0, right: 0, textAlign: 'center'}}>
				<ClipReveal delay={76} stiffness={66} damping={242}>
					<div
						style={{
							color: WHITE,
							fontSize: 252,
							fontWeight: 900,
							lineHeight: 0.80,
							letterSpacing: -14,
							textAlign: 'center',
						}}
					>
						14
					</div>
				</ClipReveal>
			</div>

			{/* ══════════════════════════════
			    7. "MARS" — clip-reveal
			    ══════════════════════════════ */}
			<div style={{position: 'absolute', top: 998, left: 0, right: 0, textAlign: 'center'}}>
				<ClipReveal delay={85} stiffness={70} damping={232}>
					<div
						style={{
							color: WHITE,
							fontSize: 142,
							fontWeight: 900,
							lineHeight: 0.90,
							letterSpacing: 10,
							textAlign: 'center',
						}}
					>
						MARS
					</div>
				</ClipReveal>
			</div>

			{/* ══════════════════════════════
			    8. HORAIRES — "10H — 16H"
			    ══════════════════════════════ */}
			<FadeSlide
				delay={96}
				fromY={10}
				targetOpacity={0.65}
				style={{
					position: 'absolute',
					top: 1156,
					left: 0,
					right: 0,
					textAlign: 'center',
					color: WHITE,
					fontSize: 34,
					fontWeight: 400,
					fontFamily: 'Arial, Helvetica, sans-serif',
					letterSpacing: 8,
					textTransform: 'uppercase',
				}}
			>
				10h — 16h
			</FadeSlide>

			{/* ══════════════════════════════
			    9. LIGNE SÉPARATRICE
			    ══════════════════════════════ */}
			<LineDraw
				delay={108}
				lineOpacity={0.20}
				style={{position: 'absolute', top: 1222, left: 56, right: 56}}
			/>

			{/* ══════════════════════════════
			    10. PANNEAU "MARCHÉ DE L'ART"
			    ══════════════════════════════ */}
			<PanelReveal
				delay={118}
				style={{
					position: 'absolute',
					top: 1250,
					left: 0,
					right: 0,
					background: WHITE,
					paddingTop: 30,
					paddingBottom: 30,
					paddingLeft: 44,
					paddingRight: 44,
				}}
			>
				<ClipReveal delay={122} stiffness={86} damping={208}>
					<div
						style={{
							color: RED,
							fontSize: 40,
							fontWeight: 900,
							textTransform: 'uppercase',
							lineHeight: 1,
							letterSpacing: 0.5,
							textAlign: 'center',
							fontStyle: 'italic',
						}}
					>
						MARCHÉ DE L'ART · CULTURE · LUXE
					</div>
				</ClipReveal>
			</PanelReveal>

			{/* ══════════════════════════════
			    11. CTA — "RÉSERVE TA PLACE !"
			    ══════════════════════════════ */}
			<FadeSlide
				delay={144}
				fromY={22}
				style={{
					position: 'absolute',
					top: 1398,
					left: 0,
					right: 0,
				}}
			>
				<div style={{transform: `scale(${ctaPulse})`}}>
					<div
						style={{
							background: WHITE,
							paddingTop: 33,
							paddingBottom: 33,
							textAlign: 'center',
						}}
					>
						<ClipReveal delay={149} stiffness={90} damping={202}>
							<div
								style={{
									color: NAVY,
									fontSize: 52,
									fontWeight: 900,
									letterSpacing: 1,
									textTransform: 'uppercase',
								}}
							>
								RÉSERVE TA PLACE !
							</div>
						</ClipReveal>
					</div>
				</div>
			</FadeSlide>

			{/* ══════════════════════════════
			    12. ADRESSE — pied de page
			    ══════════════════════════════ */}
			<FadeSlide
				delay={176}
				fromY={8}
				targetOpacity={0.50}
				style={{
					position: 'absolute',
					bottom: 86,
					left: 0,
					right: 0,
					textAlign: 'center',
					color: WHITE,
					fontSize: 22,
					fontWeight: 400,
					fontFamily: 'Arial, Helvetica, sans-serif',
					letterSpacing: 3.5,
					textTransform: 'uppercase',
				}}
			>
				13 rue Miollis · 75015 Paris
			</FadeSlide>
		</AbsoluteFill>
	);
};
