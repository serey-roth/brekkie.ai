import { motion } from 'framer-motion';
import { AlertCircle } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useSupabaseAuth } from '@/hooks/use-supabase-auth';

export function AuthForm() {
    const [isLoading, setIsLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const { loginWithGoogle } = useSupabaseAuth();

    const handleGoogleLogin = async () => {
        try {
            setIsLoading(true);
            setErrorMessage(null);
            await loginWithGoogle();
        } catch (error) {
            setErrorMessage(error instanceof Error ? error.message : 'Failed to login with Google');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="bg-background-light flex min-h-screen">
            {/* Left side - Auth Form */}
            <div className="flex w-full flex-col items-center justify-center p-4 lg:w-1/3 lg:p-8">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="w-full max-w-md"
                >
                    {/* Logo and Header */}
                    <div className="mb-6 text-center">
                        <motion.div
                            initial={{ scale: 0.8 }}
                            animate={{ scale: 1 }}
                            transition={{ duration: 0.5, delay: 0.2 }}
                            className="mb-12 inline-flex items-center justify-center gap-3"
                        >
                            <Link to="/" className="inline-flex items-center justify-center gap-3">
                                <img
                                    src="/brekkie-logo.png"
                                    alt="Brekkie Logo"
                                    className="h-12 w-12"
                                />
                                <h1 className="text-contrast text-2xl font-medium">brekkie.ai</h1>
                            </Link>
                        </motion.div>
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.4 }}
                            className="mb-4"
                        >
                            <h2 className="text-contrast mb-2 text-3xl leading-tight font-medium">
                                Chat with Milo
                            </h2>
                            <p className="text-contrast-subtle text-base">
                                Your AI food buddy for cooking, recipes, and all things food.
                            </p>
                        </motion.div>
                    </div>

                    <motion.button
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.3 }}
                        onClick={handleGoogleLogin}
                        disabled={isLoading}
                        className="bg-background border-border text-contrast hover:bg-primary/10 hover:border-primary focus:ring-primary mb-4 flex w-full items-center justify-center gap-3 rounded-lg border px-4 py-3 font-medium transition-colors focus:ring-2 focus:ring-offset-2 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        <svg className="h-5 w-5" viewBox="0 0 24 24">
                            <path
                                fill="#4285F4"
                                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                            />
                            <path
                                fill="#34A853"
                                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                            />
                            <path
                                fill="#FBBC05"
                                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                            />
                            <path
                                fill="#EA4335"
                                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                            />
                        </svg>
                        {isLoading ? 'Signing in...' : 'Continue with Google'}
                    </motion.button>

                    {errorMessage && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="mb-4 flex items-start gap-2"
                        >
                            <AlertCircle className="text-error mt-0.5 h-4 w-4 flex-shrink-0" />
                            <p className="text-error text-sm">{errorMessage}</p>
                        </motion.div>
                    )}

                    {/* Legal Disclaimer */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.5, delay: 0.6 }}
                        className="mt-6 text-center"
                    >
                        <p className="text-contrast-subtle text-xs">
                            By continuing, you agree to our{' '}
                            <a
                                href="https://meet-brekkie-ai.vercel.app/terms"
                                className="hover:text-contrast underline transition-colors"
                            >
                                Terms of Service
                            </a>{' '}
                            and acknowledge our{' '}
                            <a
                                href="https://meet-brekkie-ai.vercel.app/privacy"
                                className="hover:text-contrast underline transition-colors"
                            >
                                Privacy Policy
                            </a>
                            .
                        </p>
                    </motion.div>
                </motion.div>
            </div>

            {/* Right side - Demo (only visible on lg and larger) */}
            <div className="lg:from-primary/5 lg:to-primary/10 hidden lg:flex lg:w-2/3 lg:flex-col lg:items-center lg:justify-center lg:bg-gradient-to-br lg:p-8">
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.7, delay: 0.3 }}
                    className="w-full max-w-4xl"
                >
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.5 }}
                        className="bg-background relative overflow-hidden rounded-xl shadow-2xl"
                    >
                        <video
                            src="/brekkie-ai.mp4"
                            autoPlay
                            loop
                            muted
                            playsInline
                            preload="auto"
                            style={{
                                width: '100%',
                                height: '100%',
                                objectFit: 'contain',
                                backgroundColor: 'transparent',
                                transform: 'scaleY(1.06) scaleX(1.01)',
                            }}
                        />
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.5, delay: 0.8 }}
                        className="mt-4 text-center"
                    >
                        <p className="text-contrast-subtle text-xs">
                            Demo video showing Milo's capabilities. Actual experience may vary.
                        </p>
                    </motion.div>
                </motion.div>
            </div>
        </div>
    );
}
