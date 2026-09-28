/**
 * Onboarding wizard for first-time users
 * Interactive 5-step tour explaining the Terminal
 */
import { useState } from 'react';

const STEPS = [
    {
        title: 'Welcome to Aeon Analysis',
        description: 'A unified financial workstation connecting multiple analysis engines. Everything runs locally on your machine.',
        icon: '🚀',
    },
    {
        title: 'One Ticker, Every Engine',
        description: 'Enter a ticker in the top search bar. All tabs (Markets, Agents, Reports) react to it automatically.',
        icon: '🎯',
    },
    {
        title: 'Fusion Analysis',
        description: 'Our proprietary Fusion tab combines OpenBB market data, agent debates, and quant models into one unified view.',
        icon: '⚡',
    },
    {
        title: 'Service Status',
        description: 'Green dots in the nav mean services are running. If any are down, check the setup guide to start them.',
        icon: '🟢',
    },
    {
        title: 'Start Exploring',
        description: 'Try typing AAPL, MSFT, or TSLA to see the Terminal in action. Use / to jump to the search bar anytime.',
        icon: '✨',
    },
];

export default function Onboarding() {
    const [step, setStep] = useState(0);
    const [show, setShow] = useState(() => {
        // Show onboarding only on first visit
        return !localStorage.getItem('aeonnimbus_onboarding_completed');
    });

    if (!show) return null;

    const currentStep = STEPS[step];
    const isLast = step === STEPS.length - 1;

    const handleNext = () => {
        if (isLast) {
            localStorage.setItem('aeonnimbus_onboarding_completed', 'true');
            setShow(false);
        } else {
            setStep(step + 1);
        }
    };

    const handleSkip = () => {
        localStorage.setItem('aeonnimbus_onboarding_completed', 'true');
        setShow(false);
    };

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.92)',
            backdropFilter: 'blur(8px)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
        }}>
            <div className="card-premium animate-fade-in" style={{
                borderRadius: '16px',
                padding: '48px',
                maxWidth: '560px',
                width: '100%',
                textAlign: 'center',
            }}>
                <div style={{ fontSize: '64px', marginBottom: '24px' }}>
                    {currentStep.icon}
                </div>

                <h2 className="text-2xl font-bold mb-4 text-accent">
                    {currentStep.title}
                </h2>

                <p className="text-base leading-relaxed mb-8 text-ink2">
                    {currentStep.description}
                </p>

                {/* Progress dots */}
                <div className="flex justify-center gap-2 mb-8">
                    {STEPS.map((_, idx) => (
                        <div key={idx} style={{
                            width: '8px',
                            height: '8px',
                            borderRadius: '50%',
                            background: idx === step ? 'var(--gold)' : 'var(--rule2)',
                            transition: 'background 0.2s',
                        }} />
                    ))}
                </div>

                <div className="flex justify-center gap-3">
                    <button onClick={handleSkip} className="btn-secondary">
                        Skip Tour
                    </button>
                    <button onClick={handleNext} className="btn-primary" style={{ padding: '12px 32px' }}>
                        {isLast ? 'Get Started' : 'Next'}
                    </button>
                </div>
            </div>
        </div>
    );
}
