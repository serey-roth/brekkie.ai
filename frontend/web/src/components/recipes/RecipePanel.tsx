import { AnimatePresence, motion } from 'framer-motion';
import { ArrowRightFromLine } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useRecipeManager } from '@/context/chat-context';
import type { UserRecipe } from '@/data/schemas/recipes';
import { RecipeView } from './RecipeView';

interface RecipePanelProps {
    selectedRecipeId: string | null;
    isSidebarOpen: boolean;
    onClose: () => void;
}

export function RecipePanel({ selectedRecipeId, isSidebarOpen, onClose }: RecipePanelProps) {
    const [recipe, setRecipe] = useState<UserRecipe | undefined>(undefined);

    const recipeManager = useRecipeManager();

    useEffect(() => {
        const recipeUpdatedListener = (recipe: UserRecipe) => {
            if (recipe.id === selectedRecipeId) {
                setRecipe(recipe);
            }
        };
        recipeManager.subscribe('recipeUpdated', recipeUpdatedListener);
        return () => {
            recipeManager.unsubscribe('recipeUpdated', recipeUpdatedListener);
        };
    }, [selectedRecipeId, recipeManager]);

    useEffect(() => {
        if (selectedRecipeId === null) {
            setRecipe(undefined);
        } else {
            setRecipe(recipeManager.getRecipe(selectedRecipeId));
        }
    }, [selectedRecipeId, recipeManager]);

    return (
        <AnimatePresence mode="wait">
            {selectedRecipeId !== null && (
                <motion.div
                    initial={{ x: '100%', opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    exit={{ x: '100%', opacity: 0 }}
                    transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                    className={`fixed right-0 bottom-0 left-0 z-30 overflow-y-auto bg-white lg:relative lg:z-auto lg:col-span-1 lg:block ${isSidebarOpen ? 'md:left-[20rem]' : 'md:left-14'} lg:left-0`}
                >
                    <div className="bg-background-light pb-safe pt-safe px-safe h-full">
                        <div className="border-border custom-scrollbar mx-auto h-screen max-h-screen overflow-y-auto rounded-lg border-l p-4 shadow-lg">
                            <div className="mb-6 ml-12 flex justify-start md:ml-0">
                                <button
                                    onClick={onClose}
                                    className="text-contrast hover:text-primary hover:bg-primary/10 focus:ring-primary/20 flex h-10 w-10 items-center justify-center rounded-xl border-none shadow-none backdrop-blur-sm transition-colors duration-200 focus:ring-0 focus:outline-none md:flex"
                                >
                                    <ArrowRightFromLine
                                        className="transition-transform duration-200"
                                        size={20}
                                    />
                                </button>
                            </div>
                            <RecipeView recipe={recipe} isOpen={selectedRecipeId !== null} />
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
