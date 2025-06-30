import { motion, AnimatePresence } from 'framer-motion';
import { useCallback, useEffect, useMemo, useState, type ReactElement } from 'react';
import React from 'react';
import { FaClock, FaUserFriends, FaFire, FaChevronDown } from 'react-icons/fa';
import { Markdown } from '@/components/ui/Markdown';
import {
    type RecipeCategory,
    type RecipeIngredient,
    type RecipeInstruction,
    type UserRecipe,
} from '@/data/schemas/recipes';
import { formatRecipeCategory, formatRecipeTime } from '@/utils/recipe-utils';

type RecipeViewProps = {
    recipe: Partial<UserRecipe> | undefined;
    isOpen: boolean;
};

type Tab = 'ingredients' | 'instructions';
type NotesTab = 'prep' | 'serving' | 'storage';

export function RecipeView({ recipe, isOpen }: RecipeViewProps) {
    const name = useMemo(() => recipe?.name ?? '', [recipe?.name]);
    const description = useMemo(() => recipe?.description ?? '', [recipe?.description]);
    const categories = useMemo(() => recipe?.categories ?? [], [recipe?.categories]);
    const prep_time_minutes = useMemo(() => recipe?.prep_time_minutes ?? 0, [recipe?.prep_time_minutes]);
    const cook_time_minutes = useMemo(() => recipe?.cook_time_minutes ?? 0, [recipe?.cook_time_minutes]);
    const servings = useMemo(() => recipe?.servings ?? '', [recipe?.servings]);
    const ingredients = useMemo(() => recipe?.ingredients ?? [], [recipe?.ingredients]);
    const instructions = useMemo(() => recipe?.instructions ?? [], [recipe?.instructions]);
    const notes: RecipeNote[] = useMemo(() => [
        { key: 'chef_notes', label: "Chef's Notes", content: recipe?.chef_notes },
        { key: 'make_ahead_tips', label: 'Make Ahead Tips', content: recipe?.make_ahead_tips },
        { key: 'equipment_alternatives', label: 'Equipment Alternatives', content: recipe?.equipment_alternatives },
        { key: 'coordination_timeline', label: 'Timeline', content: recipe?.coordination_timeline },
        { key: 'scaling_guidance', label: 'Scaling Guidance', content: recipe?.scaling_guidance },
        { key: 'storage_notes', label: 'Storage Notes', content: recipe?.storage_notes },
        { key: 'serving_suggestions', label: 'Serving Suggestions', content: recipe?.serving_suggestions },
        { key: 'substitutions', label: 'Substitutions', content: recipe?.substitutions },
    ].filter(note => !!note.content), [
        recipe?.chef_notes,
        recipe?.make_ahead_tips,
        recipe?.equipment_alternatives,
        recipe?.coordination_timeline,
        recipe?.scaling_guidance,
        recipe?.storage_notes,
        recipe?.serving_suggestions,
        recipe?.substitutions,
    ]);

    const [activeTab, setActiveTab] = useState<Tab>('ingredients');

    useEffect(() => {
        if (!instructions.length) {
            setActiveTab('ingredients');
        } else {
            setActiveTab('instructions');
        }
    }, [ingredients, instructions]);

    const handleTabChange = useCallback((tab: Tab) => {
        setActiveTab(tab);
    }, [])  ;

    return (
        <AnimatePresence mode="wait">
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ 
                        duration: 0.4,
                        ease: [0.4, 0, 0.2, 1],
                        opacity: { duration: 0.3 }
                    }}
                    className="overflow-hidden"
                >
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ 
                            duration: 0.3,
                            delay: 0.15,
                            ease: [0.4, 0, 0.2, 1]
                        }}
                    >
                        <RecipeHeader name={name} description={description} />
                        {categories.length > 0 && <RecipeCategories categories={categories} />}
                        <RecipeMeta
                            prep_time_minutes={prep_time_minutes}
                            cook_time_minutes={cook_time_minutes}
                            servings={servings}
                        />
                        <RecipeTabs activeTab={activeTab} setActiveTab={handleTabChange} />
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={activeTab}
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -8 }}
                                transition={{ 
                                    duration: 0.3,
                                    ease: [0.4, 0, 0.2, 1]
                                }}
                            >
                                {activeTab === 'ingredients' ? (
                                    <IngredientsList ingredients={ingredients} />
                                ) : (
                                    <InstructionsList instructions={instructions} />
                                )}
                            </motion.div>
                        </AnimatePresence>
                        <GroupedRecipeNotesTabs notes={notes} />
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}

// -----------------------------
// Memoized Subcomponents
// -----------------------------

const RecipeHeader = React.memo(function RecipeHeader({ name, description }: { name?: string; description?: string }) {
    return (
        <motion.header
            initial="hidden"
            animate="visible"
            variants={{
                hidden: {},
                visible: {
                    transition: {
                        staggerChildren: 0.05,
                    },
                },
            }}
            className="mb-6"
        >
            <motion.h1 
                variants={{
                    hidden: { opacity: 0, y: 20 },
                    visible: { opacity: 1, y: 0 },
                }}
                transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
                className="text-contrast mb-2 font-serif text-4xl font-semibold"
            >
                <Markdown>{name ?? ''}</Markdown>
            </motion.h1>
            {description && (
                <motion.p 
                    variants={{
                        hidden: { opacity: 0, y: 20 },
                        visible: { opacity: 1, y: 0 },
                    }}
                    transition={{ duration: 0.4, delay: 0.1, ease: [0.4, 0, 0.2, 1] }}
                    className="text-contrast-subtle text-base"
                >
                    <Markdown>{description}</Markdown>
                </motion.p>
            )}
        </motion.header>
    );
});

const RecipeCategories = React.memo(function RecipeCategories({ categories }: { categories: RecipeCategory[] }) {
    return (
        <motion.div
            initial="hidden"
            animate="visible"
            variants={{
                hidden: {},
                visible: {
                    transition: {
                        staggerChildren: 0.03,
                    },
                },
            }}
            className="mb-6 flex flex-wrap gap-2"
        >
            {categories.map((cat) => (
                <motion.span
                    key={cat.name}
                    variants={{
                        hidden: { opacity: 0, y: 6 },
                        visible: { opacity: 1, y: 0 },
                    }}
                    transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
                    className="border-primary bg-background text-primary rounded-full border px-4 py-1 text-sm font-semibold"
                >
                    {formatRecipeCategory(cat.name)}
                </motion.span>
            ))}
        </motion.div>
    );
});

const RECIPE_META_ICONS = {
    prep_time: <FaClock className="text-primary-dark" />,    
    cook_time: <FaFire className="text-primary-dark" />,
    servings: <FaUserFriends className="text-primary-dark" />,
} as const;


const RecipeMeta = React.memo(function RecipeMeta({
    prep_time_minutes,
    cook_time_minutes,
    servings,
}: {
    prep_time_minutes?: number;
    cook_time_minutes?: number;
    servings?: string;
}) {
    const metaItems: { icon: ReactElement; prefix?: string; suffix?: string; text: string | undefined }[] = useMemo(() => {
        return [
            { icon: RECIPE_META_ICONS.prep_time, prefix: 'Prep', text: prep_time_minutes ? formatRecipeTime(prep_time_minutes) : undefined },
            { icon: RECIPE_META_ICONS.cook_time, prefix: 'Cook', text: cook_time_minutes ? formatRecipeTime(cook_time_minutes) : undefined },
            { icon: RECIPE_META_ICONS.servings, suffix: 'servings', text: servings },
        ].filter(item => !!item.text);
    }, [prep_time_minutes, cook_time_minutes, servings]);   

    return (
        <motion.section
            initial="hidden"
            animate="visible"
            variants={{
                hidden: {},
                visible: {
                    transition: { staggerChildren: 0.05 },
                },
            }}
            className="text-contrast-subtle mb-8 flex flex-wrap gap-6 text-sm"
        >
            {metaItems.map((item, idx) => (
                <motion.div
                    key={idx}
                    variants={{
                        hidden: { opacity: 0, y: 6 },
                        visible: { opacity: 1, y: 0 },
                    }}
                    transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
                    className="flex items-center gap-1.5"
                >
                    {item.icon}
                    <span className="text-contrast-subtle text-sm">
                        {item.prefix ? `${item.prefix}: ` : ''}
                        {item.text}
                        {item.suffix ? ` ${item.suffix}` : ''}
                    </span>
                </motion.div>
            ))}
        </motion.section>
    );
});

const RecipeTabs = React.memo(function RecipeTabs({
    activeTab,
    setActiveTab,
}: {
    activeTab: Tab;
    setActiveTab: (tab: Tab) => void;
}) {
    const tabs: Tab[] = ['ingredients', 'instructions'];
    return (
        <nav className="border-border mb-6 flex border-b">
            {tabs.map(tab => (
                <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`border-b-2 px-6 py-2 text-base font-medium transition-colors ${
                        activeTab === tab
                            ? 'text-primary border-primary'
                            : 'text-contrast-subtle hover:text-primary border-transparent'
                    }`}
                >
                    {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
            ))}
        </nav>
    );
});

const IngredientsList = React.memo(function IngredientsList({ ingredients }: { ingredients: RecipeIngredient[] }) {
    return (
        <ul className="space-y-2">
            {ingredients.map((ingredient, i) => (
                <motion.li
                    layout
                    key={`${ingredient.name}-${i}`}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ 
                        duration: 0.25,
                        delay: i * 0.03,
                        ease: [0.4, 0, 0.2, 1]
                    }}
                    className="text-contrast flex items-baseline text-base"
                >
                    <span className="text-primary bg-primary mr-4 inline-block h-1.5 w-1.5 rounded-full"></span>
                    <span>
                        {ingredient.name}
                        {(ingredient.quantity || ingredient.unit) && (
                            <span className="text-contrast-subtle ml-2">
                                {ingredient.quantity} {ingredient.unit}
                            </span>
                        )}
                    </span>
                </motion.li>
            ))}
        </ul>
    );
});

const InstructionsList = React.memo(function InstructionsList({ instructions }: { instructions: RecipeInstruction[] }) {
    const [openSteps, setOpenSteps] = useState<Record<string, boolean>>({});

    useEffect(() => {
        const initial: Record<string, boolean> = {};
        if (instructions.length > 0) {
            initial[instructions[0].title] = true;
        }
        setOpenSteps(initial);
    }, [instructions]);

    const toggleStep = (step: string) => {
        setOpenSteps(prev => ({ ...prev, [step]: !prev[step] }));
    };

    return (
        <ol className="space-y-1">
            {instructions.map(({ title, description }, i) => {
                const isOpen = openSteps[title];
                const hasContent = !!description?.trim();

                return (
                    <motion.li
                        key={`${title}`}
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ 
                            duration: 0.25,
                            delay: i * 0.04,
                            ease: [0.4, 0, 0.2, 1]
                        }}
                        className="group bg-background cursor-pointer rounded-lg transition-all duration-200 border border-transparent hover:border-primary/50"
                        onClick={() => hasContent && toggleStep(title)}
                    >
                        <div className="flex items-center justify-between px-4 py-3">
                            <div className="flex items-center gap-4">
                                <div className="bg-primary flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-sm text-white">
                                    {i + 1}
                                </div>
                                <h3 className="text-contrast truncate text-base font-medium">{title}</h3>
                            </div>
                            {hasContent && (
                                <FaChevronDown
                                    className={`text-primary-dark transition-transform duration-200 ${
                                        isOpen ? 'rotate-180' : ''
                                    } group-hover:text-primary`}
                                    onClick={e => {
                                        e.stopPropagation();
                                        toggleStep(title);
                                    }}
                                />
                            )}
                        </div>
                        <AnimatePresence mode="wait">
                            {isOpen && hasContent && (
                                <motion.div
                                    key={`desc-${title}`}
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    exit={{ opacity: 0, height: 0 }}
                                    transition={{ 
                                        duration: 0.3,
                                        ease: [0.4, 0, 0.2, 1],
                                        opacity: { duration: 0.25 }
                                    }}
                                    className="overflow-hidden"
                                >
                                    <div className="text-contrast px-4 pt-1 pb-4 text-sm">{description}</div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.li>
                );
            })}
        </ol>
    );
});

type RecipeNote = {
    key: string;
    label: string;
    content: string | undefined | null;
};

const groupedNotes = [
    {
        id: 'prep',
        label: 'Prep Notes',
        keys: ['chef_notes', 'make_ahead_tips', 'equipment_alternatives', 'coordination_timeline'],
    },
    {
        id: 'serving',
        label: 'Serving & Scaling',
        keys: ['serving_suggestions', 'scaling_guidance'],
    },
    {
        id: 'storage',
        label: 'Storage & Substitutions',
        keys: ['storage_notes', 'substitutions'],
    },
];

export const GroupedRecipeNotesTabs = ({
    notes,
}: {
    notes: { key: string; label: string; content: string | undefined | null }[];
}) => {
    const [activeTab, setActiveTab] = useState<NotesTab>('prep');
    const [openNotes, setOpenNotes] = useState<Record<string, boolean>>({});

    const toggleNote = (key: string) =>
        setOpenNotes(prev => ({ ...prev, [key]: !prev[key] }));

    const notesMap = useMemo(() => {
        return notes.reduce((map, note) => {
            map[note.key] = note;
            return map;
        }, {} as Record<string, { key: string; label: string; content: string | null | undefined }>);
    }, [notes]);

    const currentGroup = groupedNotes.find(g => g.id === activeTab);
    const groupNotes = (currentGroup?.keys ?? []).map(k => notesMap[k]).filter(Boolean);

    useEffect(() => {
        const hasAllPrepNotes = groupedNotes[0].keys.every(k => notesMap[k]?.content);
        const hasAllServingNotes = groupedNotes[1].keys.every(k => notesMap[k]?.content);
        const hasAllStorageNotes = groupedNotes[2].keys.every(k => notesMap[k]?.content);

        if (hasAllPrepNotes && !hasAllServingNotes) {
            setActiveTab('serving');
        } else if (hasAllServingNotes && !hasAllStorageNotes) {
            setActiveTab('storage');
        } else {
            setActiveTab('prep');
        }
    }, [notesMap]);

    if (groupNotes.length === 0) return null;

    return (
        <section className="mt-10 w-full">
            <h2 className="text-contrast mb-4 font-serif text-2xl font-semibold">Additional Notes</h2>
            <nav className="border-border mb-6 flex border-b">
                {groupedNotes.map(tab => (
                    <button
                        key={`${tab.id}-${tab.label}`}
                        onClick={() => setActiveTab(tab.id as NotesTab)}
                        className={`border-b-2 px-6 py-2 text-base font-medium transition-colors ${
                            activeTab === tab.id
                                ? 'text-primary border-primary'
                                : 'text-contrast-subtle hover:text-primary border-transparent'
                        }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </nav>

            <AnimatePresence mode="wait">
                <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ 
                        duration: 0.3,
                        ease: [0.4, 0, 0.2, 1]
                    }}
                >
                    <ul className="space-y-1">
                        {groupNotes.map((note, i) => {
                            const isOpen = openNotes[note.key];
                            const hasContent = !!note.content?.trim();

                            return (
                                <motion.li
                                    key={`${note.key}-${note.label}`}
                                    initial={{ opacity: 0, y: 4 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ 
                                        duration: 0.25,
                                        delay: i * 0.04,
                                        ease: [0.4, 0, 0.2, 1]
                                    }}
                                    className="group bg-background cursor-pointer rounded-lg transition-all duration-200 border border-transparent hover:border-primary/50"
                                    onClick={() => hasContent && toggleNote(note.key)}
                                >
                                    <div className="flex items-center justify-between px-4 py-3">
                                        <div className="flex items-center gap-4">
                                            <h3 className={`text-base font-medium transition-colors duration-200 ${
                                                isOpen ? 'text-primary' : 'text-contrast'
                                            }`}>
                                                {note.label}
                                            </h3>
                                        </div>
                                        {hasContent && (
                                            <FaChevronDown
                                                className={`text-primary-dark transition-all duration-200 ${
                                                    isOpen ? 'rotate-180 text-primary' : ''
                                                } group-hover:text-primary`}
                                                onClick={e => {
                                                    e.stopPropagation();
                                                    toggleNote(note.key);
                                                }}
                                            />
                                        )}
                                    </div>
                                    <AnimatePresence mode="wait">
                                        {isOpen && hasContent && (
                                            <motion.div
                                                key={`desc-${note.key}`}
                                                initial={{ opacity: 0, height: 0 }}
                                                animate={{ opacity: 1, height: 'auto' }}
                                                exit={{ opacity: 0, height: 0 }}
                                                transition={{ 
                                                    duration: 0.3,
                                                    ease: [0.4, 0, 0.2, 1],
                                                    opacity: { duration: 0.25 }
                                                }}
                                                className="overflow-hidden"
                                            >
                                                <div className="text-contrast px-4 pt-1 pb-4 text-sm border-t border-border">
                                                    <Markdown>{note.content ?? ''}</Markdown>
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </motion.li>
                            );
                        })}
                    </ul>
                </motion.div>
            </AnimatePresence>
        </section>
    );
};
