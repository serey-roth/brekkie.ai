import { useRecipeConversationSimulation } from '@/hooks/use-recipe-conversation-simulation';

export function ConversationSimulationTest() {
    const { startSimulation, isRunning, isCompleted } = useRecipeConversationSimulation();

    return (
        <div className="rounded-lg bg-white p-4 shadow-md">
            <h2 className="mb-4 text-xl font-semibold">Conversation Simulation Test</h2>
            <div className="space-y-2">
                <button
                    onClick={startSimulation}
                    disabled={isRunning}
                    className="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600 disabled:bg-gray-400"
                >
                    {isRunning ? 'Simulation Running...' : 'Start Mediterranean Pasta Conversation'}
                </button>
                {isCompleted && (
                    <p className="font-medium text-green-600">
                        ✅ Conversation simulation completed! Check the chat for the Mediterranean
                        pasta recipe.
                    </p>
                )}
                {isRunning && (
                    <p className="text-blue-600">🔄 Running conversation simulation...</p>
                )}
            </div>
        </div>
    );
}
