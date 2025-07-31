import { AnimatePresence, motion } from 'framer-motion';
import { Utensils, CircleAlert, LoaderCircle } from 'lucide-react';
import { DateTime } from 'luxon';
import { Masonry } from 'masonic';
import { useCallback, useEffect, useState, useMemo, useRef } from 'react';
import { useAppState, useRecipesApiClient } from '@/context/app-context';
import { useRecipeManager } from '@/context/chat-context';
import type { UserRecipe } from '@/data/schemas/recipes';
import { RecipeCard } from '../recipes/RecipeCard';

export const RecipeListView = () => {
    const [recipes, setRecipes] = useState<UserRecipe[]>([]);
    const [loadingState, setLoadingState] = useState<'idle' | 'loading' | 'success' | 'error'>(
        'idle',
    );
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);

    const { selectedRecipeId, setSelectedRecipeId } = useAppState();

    const recipeManager = useRecipeManager();
    const recipesApiClient = useRecipesApiClient();

    // Group recipes by month
    const groupedRecipes = useMemo(() => {
        const groups: { [key: string]: UserRecipe[] } = {};

        recipes
            .sort(
                (a, b) =>
                    DateTime.fromISO(b.created_at).toMillis() -
                    DateTime.fromISO(a.created_at).toMillis(),
            )
            .forEach((recipe) => {
                const date = DateTime.fromISO(recipe.created_at);
                const monthKey = date.toFormat('yyyy-MM');

                if (!groups[monthKey]) {
                    groups[monthKey] = [];
                }
                groups[monthKey].push(recipe);
            });

        return Object.entries(groups)
            .sort(([a], [b]) => b.localeCompare(a)) // Sort months descending
            .map(([monthKey, recipes]) => ({
                monthKey,
                date: DateTime.fromFormat(monthKey + '-01', 'yyyy-MM-dd'), // First day of the month
                recipes,
            }));
    }, [recipes]);

    const formatMonth = (date: DateTime) => {
        const now = DateTime.now();
        const currentMonth = now.startOf('month');
        const lastMonth = now.minus({ months: 1 }).startOf('month');

        if (date.hasSame(currentMonth, 'month')) {
            return 'This Month';
        } else if (date.hasSame(lastMonth, 'month')) {
            return 'Last Month';
        } else {
            return date.toFormat('MMMM yyyy');
        }
    };

    const fetchRecipes = useCallback(async () => {
        setLoadingState('loading');
        setErrorMessage(null);

        try {
            const userRecipes = await recipesApiClient.getUserRecipes();
            setRecipes(userRecipes);
            recipeManager.addRecipes(userRecipes);
            setLoadingState('success');
        } catch (error) {
            console.error('Failed to fetch recipes:', error);
            setErrorMessage('Failed to load your recipes. Please try again.');
            setLoadingState('error');
        }
    }, [recipeManager, recipesApiClient]);

    useEffect(() => {
        fetchRecipes();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <motion.div
            className={`relative ${selectedRecipeId ? 'col-span-1' : 'w-full lg:col-span-1 lg:mx-auto'}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{
                type: 'spring',
                damping: 30,
                stiffness: 300,
                duration: 0.4,
            }}
        >
            <motion.div
                className="relative mx-auto flex h-screen flex-col items-center overflow-hidden"
                initial={{ scale: 0.98, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.98, opacity: 0 }}
                transition={{
                    type: 'spring',
                    damping: 25,
                    stiffness: 200,
                    duration: 0.3,
                    delay: 0.1,
                }}
            >
                {/* Header */}
                <motion.div
                    className="bg-background/95 border-border/50 absolute top-0 right-0 left-0 z-10 h-20 w-full border-b shadow-sm backdrop-blur-sm"
                    initial={{ y: -20, opacity: 0, width: '100%' }}
                    animate={{ y: 0, opacity: 1, width: '100%' }}
                    exit={{ y: -20, opacity: 0, width: '100%' }}
                    transition={{
                        duration: 0.4,
                        ease: 'easeOut',
                        delay: 0.1,
                    }}
                >
                    <div className="flex items-center justify-between px-4 py-4 pl-16 md:px-8 md:py-6 md:pl-4">
                        <motion.span
                            className="text-contrast text-xl font-semibold"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ delay: 0.2 }}
                        >
                            Cookbook
                        </motion.span>
                    </div>
                </motion.div>

                {/* Scrollable Content */}
                <motion.div
                    ref={scrollRef}
                    className="custom-scrollbar w-full max-w-3xl flex-1 overflow-y-auto px-4 pt-[100px] pb-4 transition-all duration-300 ease-out"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <div className="mx-auto w-full max-w-4xl px-4 md:px-8">
                        <AnimatePresence mode="wait">
                            {loadingState === 'loading' && (
                                <motion.div
                                    key="loading"
                                    initial={{ opacity: 0, y: 30 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -30 }}
                                    transition={{
                                        type: 'spring',
                                        damping: 25,
                                        stiffness: 200,
                                        duration: 0.4,
                                    }}
                                    className="flex flex-col items-center justify-center py-16"
                                >
                                    <motion.div
                                        transition={{
                                            duration: 1,
                                            repeat: Infinity,
                                            ease: 'linear',
                                        }}
                                    >
                                        <LoaderCircle className="text-primary mb-4 h-8 w-8 animate-spin" />
                                    </motion.div>
                                    <motion.p
                                        className="text-contrast-subtle text-sm"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ delay: 0.2 }}
                                    >
                                        Loading your recipes...
                                    </motion.p>
                                </motion.div>
                            )}

                            {loadingState === 'error' && (
                                <motion.div
                                    key="error"
                                    initial={{ opacity: 0, y: 30 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -30 }}
                                    transition={{
                                        type: 'spring',
                                        damping: 25,
                                        stiffness: 200,
                                        duration: 0.4,
                                    }}
                                    className="flex flex-col items-center justify-center py-16 text-center"
                                >
                                    <motion.div
                                        initial={{ scale: 0.8, opacity: 0 }}
                                        animate={{ scale: 1, opacity: 1 }}
                                        transition={{ delay: 0.1 }}
                                    >
                                        <CircleAlert className="text-primary/60 mb-4 h-12 w-12" />
                                    </motion.div>
                                    <motion.h3
                                        className="text-contrast mb-2 text-lg font-medium"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: 0.2 }}
                                    >
                                        Oops! Something went wrong
                                    </motion.h3>
                                    <motion.p
                                        className="text-contrast-subtle mb-6 max-w-md text-sm"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: 0.3 }}
                                    >
                                        {errorMessage ||
                                            "We couldn't load your recipes right now. Don't worry, we're on it!"}
                                    </motion.p>
                                    <motion.button
                                        onClick={fetchRecipes}
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        className="bg-primary hover:bg-primary-dark flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: 0.4 }}
                                    >
                                        <LoaderCircle className="h-4 w-4" />
                                        Try Again
                                    </motion.button>
                                </motion.div>
                            )}

                            {loadingState === 'success' && recipes.length === 0 && (
                                <motion.div
                                    key="empty"
                                    initial={{ opacity: 0, y: 30 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -30 }}
                                    transition={{
                                        type: 'spring',
                                        damping: 25,
                                        stiffness: 200,
                                        duration: 0.4,
                                    }}
                                    className="flex flex-col items-center justify-center py-16 text-center"
                                >
                                    <motion.div
                                        initial={{ scale: 0.8, opacity: 0 }}
                                        animate={{ scale: 1, opacity: 1 }}
                                        transition={{ delay: 0.1 }}
                                    >
                                        <Utensils className="text-primary/40 mb-6 h-16 w-16" />
                                    </motion.div>
                                    <motion.h3
                                        className="text-contrast mb-3 text-xl font-medium"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: 0.2 }}
                                    >
                                        No recipes yet!
                                    </motion.h3>
                                    <motion.p
                                        className="text-contrast-subtle mb-2 max-w-md text-sm"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: 0.3 }}
                                    >
                                        Ready to start cooking? Chat with Milo and he'll whip up
                                        some amazing recipes just for you.
                                    </motion.p>
                                </motion.div>
                            )}

                            {loadingState === 'success' && recipes.length > 0 && (
                                <motion.div
                                    key="recipes"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -20 }}
                                    transition={{
                                        type: 'spring',
                                        damping: 25,
                                        stiffness: 200,
                                        duration: 0.4,
                                    }}
                                    className="space-y-6"
                                >
                                    {groupedRecipes.map(
                                        ({ monthKey, date, recipes: groupRecipes }, groupIndex) => (
                                            <motion.div
                                                key={monthKey}
                                                initial={{ opacity: 0, y: 20 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{
                                                    duration: 0.3,
                                                    delay: groupIndex * 0.1,
                                                    type: 'spring',
                                                    damping: 25,
                                                    stiffness: 200,
                                                }}
                                                className="space-y-3"
                                            >
                                                {/* Month Header */}
                                                <motion.div
                                                    className="bg-background/95 border-border/30 flex items-center gap-2 border-b py-2 backdrop-blur-sm"
                                                    initial={{ opacity: 0, x: -20, y: -5 }}
                                                    animate={{ opacity: 1, x: 0, y: 0 }}
                                                    exit={{ opacity: 0, x: -20, y: -5 }}
                                                    transition={{
                                                        delay: groupIndex * 0.1 + 0.1,
                                                        type: 'spring',
                                                        damping: 25,
                                                        stiffness: 200,
                                                    }}
                                                >
                                                    <h2 className="text-contrast-subtle text-sm font-medium">
                                                        {formatMonth(date)}
                                                    </h2>
                                                    <motion.div
                                                        className="text-contrast-subtle bg-contrast-subtle/10 rounded-full px-2 py-1 text-sm"
                                                        initial={{ scale: 0.8, opacity: 0 }}
                                                        animate={{ scale: 1, opacity: 1 }}
                                                        exit={{ scale: 0.8, opacity: 0 }}
                                                        transition={{
                                                            delay: groupIndex * 0.1 + 0.2,
                                                            type: 'spring',
                                                            damping: 20,
                                                            stiffness: 300,
                                                        }}
                                                    >
                                                        {groupRecipes.length}
                                                    </motion.div>
                                                </motion.div>

                                                {/* Recipes Grid */}
                                                <Masonry
                                                    items={groupRecipes}
                                                    render={({ data: recipe, index }) => (
                                                        <motion.div
                                                            key={recipe.id}
                                                            initial={{ opacity: 0 }}
                                                            animate={{ opacity: 1 }}
                                                            exit={{ opacity: 0 }}
                                                            transition={{
                                                                duration: 0.4,
                                                                delay:
                                                                    groupIndex * 0.1 +
                                                                    index * 0.08 +
                                                                    0.2,
                                                                type: 'spring',
                                                                damping: 25,
                                                                stiffness: 200,
                                                            }}
                                                        >
                                                            <RecipeCard
                                                                recipe={recipe}
                                                                selectedRecipeId={selectedRecipeId}
                                                                onSelectRecipe={() =>
                                                                    setSelectedRecipeId(recipe.id)
                                                                }
                                                                className="hover:bg-contrast-subtle/80 hover:scale-[1.02] hover:shadow-lg"
                                                            />
                                                        </motion.div>
                                                    )}
                                                    columnGutter={8}
                                                    columnWidth={selectedRecipeId ? 300 : 250}
                                                    overscanBy={2}
                                                />
                                            </motion.div>
                                        ),
                                    )}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </motion.div>
            </motion.div>
        </motion.div>
    );
};
