import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { FaCircleExclamation } from 'react-icons/fa6';
import { LuEye, LuEyeOff, LuLoader, LuX } from 'react-icons/lu';
import { type UserSigninPayload, type UserSignupPayload } from '@/data/schemas/users';

type AuthMode = 'signin' | 'signup';

interface AuthScreenProps {
    isOpen: boolean;
    onClose: () => void;
    onSignIn: (payload: UserSigninPayload) => Promise<void>;
    onSignUp: (payload: UserSignupPayload) => Promise<void>;
}

export function AuthScreen({ onSignIn, onSignUp, isOpen, onClose }: AuthScreenProps) {
    const [mode, setMode] = useState<AuthMode>('signin');
    const [email, setEmail] = useState('');
    const [name, setName] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    const resetState = () => {
        setMode('signin');
        setEmail('');
        setName('');
        setPassword('');
        setConfirmPassword('');
        setError('');
        setShowPassword(false);
        setShowConfirmPassword(false);
    };

    const handleClose = () => {
        resetState();
        onClose();
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        if (!email) {
            setError('Email is required');
            return;
        }

        if (!password) {
            setError('Password is required');
            return;
        }

        if (mode === 'signup') {
            if (!name) {
                setError('Name is required');
                return;
            }
            
            if (password.length < 8) {
                setError('Password must be at least 8 characters long');
                return;
            }

            if (!confirmPassword) {
                setError('Please confirm your password');
                return;
            }
            if (password !== confirmPassword) {
                setError('Passwords do not match');
                return;
            }
        }

        try {
            setIsSubmitting(true);
            if (mode === 'signin') {
                await onSignIn({ email, password });
            } else {
                await onSignUp({ email, name, password, confirm_password: confirmPassword });
            }
            handleClose();
        } catch (error) {
            setError(error instanceof Error ? error.message : 'An error occurred. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={handleClose}
                        className="fixed inset-0 z-[100] bg-black/20 backdrop-blur-[4px]"
                    />
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        layout
                        className="fixed inset-0 z-[101] flex items-center justify-center p-2 sm:p-4"
                    >
                        <div className="relative w-full max-w-[320px] sm:max-w-md min-h-[350px] transition-all duration-300">
                            <button
                                onClick={handleClose}
                                className="text-contrast-subtle hover:text-primary absolute top-2 right-2 sm:top-4 sm:right-4 focus:outline-none"
                                aria-label="Close"
                            >
                                <LuX size={18} className="sm:w-[22px] sm:h-[22px]" />
                            </button>
                            <div className="border-border rounded-xl sm:rounded-2xl border bg-white p-3 sm:p-6 shadow-lg">
                                <div className="mb-4 sm:mb-8 text-center">
                                    <h1 className="text-contrast mb-1 sm:mb-2 text-lg sm:text-2xl font-semibold">
                                        Welcome to brekkie.ai
                                    </h1>
                                    <p className="text-contrast-subtle text-xs sm:text-sm max-w-md mx-auto">
                                        Sign in to save your chats and unlock a higher message
                                        limit.
                                    </p>
                                </div>
                                <div className="mb-3 sm:mb-6 flex gap-2 sm:gap-4">
                                    <button
                                        onClick={() => {
                                            setMode('signin');
                                            setError('');
                                        }}
                                        className={`flex-1 border-b-2 py-1 sm:py-2 text-xs sm:text-sm font-medium transition-colors ${
                                            mode === 'signin'
                                                ? 'text-primary border-primary'
                                                : 'text-contrast-subtle hover:text-primary border-transparent'
                                        }`}
                                    >
                                        Sign in
                                    </button>
                                    <button
                                        onClick={() => {
                                            setMode('signup');
                                            setError('');
                                        }}
                                        className={`flex-1 border-b-2 py-1 sm:py-2 text-xs sm:text-sm font-medium transition-colors ${
                                            mode === 'signup'
                                                ? 'text-primary border-primary'
                                                : 'text-contrast-subtle hover:text-primary border-transparent'
                                        }`}
                                    >
                                        Sign up
                                    </button>
                                </div>

                                <form onSubmit={handleSubmit} className="flex flex-col gap-2">
                                    <div>
                                        <label
                                            htmlFor="email"
                                            className="text-contrast mb-1 block text-xs sm:text-sm font-medium"
                                        >
                                            Email
                                        </label>
                                        <input
                                            type="email"
                                            id="email"
                                            value={email}
                                            onChange={e => setEmail(e.target.value)}
                                            className="bg-background border-border text-contrast placeholder-contrast-subtle focus:ring-primary/20 focus:border-primary w-full rounded-md sm:rounded-xl border px-2 sm:px-4 py-1 sm:py-2 text-xs sm:text-sm focus:ring-2 focus:outline-none"
                                            placeholder="Enter your email"
                                        />
                                    </div>

                                    <motion.div 
                                        initial={false}
                                        animate={mode === 'signup' ? { opacity: 1, height: 'auto' } : { opacity: 0, height: 0 }}
                                        transition={{ duration: 0.3, ease: 'easeInOut' }}
                                        style={{ overflow: 'hidden' }}
                                        className="pt-0"
                                    >
                                        <label
                                            htmlFor="name"
                                            className="text-contrast mb-1 block text-xs sm:text-sm font-medium"
                                        >
                                            Name
                                        </label>
                                        <input
                                            type="text"
                                            id="name"
                                            value={name}
                                            onChange={e => setName(e.target.value)}
                                            className="bg-background border-border text-contrast placeholder-contrast-subtle focus:ring-primary/20 focus:border-primary w-full rounded-md sm:rounded-xl border px-2 sm:px-4 py-1 sm:py-2 text-xs sm:text-sm focus:ring-2 focus:outline-none"
                                            placeholder="Enter your name"
                                        />
                                    </motion.div>

                                    <div>
                                        <label
                                            htmlFor="password"
                                            className="text-contrast mb-1 block text-xs sm:text-sm font-medium"
                                        >
                                            Password
                                        </label>
                                        <div className="relative">
                                            <input
                                                type={showPassword ? 'text' : 'password'}
                                                id="password"
                                                value={password}
                                                onChange={e => setPassword(e.target.value)}
                                                className="bg-background border-border text-contrast placeholder-contrast-subtle focus:ring-primary/20 focus:border-primary w-full rounded-md sm:rounded-xl border px-2 sm:px-4 py-1 sm:py-2 text-xs sm:text-sm focus:ring-2 focus:outline-none pr-8"
                                                placeholder="Enter your password"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowPassword(!showPassword)}
                                                className="absolute right-2 top-1/2 -translate-y-1/2 text-contrast-subtle hover:text-contrast focus:outline-none"
                                                aria-label={showPassword ? 'Hide password' : 'Show password'}
                                            >
                                                {showPassword ? <LuEyeOff size={16} /> : <LuEye size={16} />}
                                            </button>
                                        </div>
                                    </div>

                                    <motion.div
                                        initial={false}
                                        animate={mode === 'signup' ? { opacity: 1, height: 'auto' } : { opacity: 0, height: 0 }}
                                        transition={{ duration: 0.3, ease: 'easeInOut' }}
                                        style={{ overflow: 'hidden' }}
                                        className="pt-0"
                                    >
                                        <label
                                            htmlFor="confirmPassword"
                                            className="text-contrast mb-1 block text-xs sm:text-sm font-medium"
                                        >
                                            Confirm Password
                                        </label>
                                        <div className="relative">
                                            <input
                                                type={showConfirmPassword ? 'text' : 'password'}
                                                id="confirmPassword"
                                                value={confirmPassword}
                                                onChange={e =>
                                                    setConfirmPassword(e.target.value)
                                                }
                                                className="bg-background border-border text-contrast placeholder-contrast-subtle focus:ring-primary/20 focus:border-primary w-full rounded-md sm:rounded-xl border px-2 sm:px-4 py-1 sm:py-2 text-xs sm:text-sm focus:ring-2 focus:outline-none pr-8"
                                                placeholder="Confirm your password"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                                className="absolute right-2 top-1/2 -translate-y-1/2 text-contrast-subtle hover:text-contrast focus:outline-none"
                                                aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                                            >
                                                {showConfirmPassword ? <LuEyeOff size={16} /> : <LuEye size={16} />}
                                            </button>
                                        </div>
                                    </motion.div>

                                    {error && (
                                        <motion.p
                                            initial={{ opacity: 0, y: -10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            className="flex items-center gap-2 text-primary text-xs sm:text-sm"
                                        >
                                            <span><FaCircleExclamation className="text-red-500" /></span>
                                            <span>{error}</span>
                                        </motion.p>
                                    )}

                                    <button
                                        type="submit"
                                        className="flex items-center justify-center gap-2 from-primary to-primary/80 hover:from-primary-dark hover:to-primary focus:ring-primary/20 mt-2 w-full rounded-md sm:rounded-xl bg-gradient-to-r py-2 text-sm sm:text-base font-semibold text-white shadow-md transition-colors focus:ring-2 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                                        disabled={isSubmitting || !email || !password || (mode === 'signup' && (!name || !confirmPassword || password !== confirmPassword))}
                                    >
                                        {isSubmitting && <span><LuLoader className="h-4 w-4 animate-spin" /></span>}
                                        <span>
                                        {isSubmitting
                                            ? mode === 'signin'
                                                ? 'Signing in...'
                                                : 'Signing up...'
                                            : mode === 'signin'
                                              ? 'Sign in'
                                              : 'Sign up'}
                                        </span>
                                    </button>
                                </form>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
