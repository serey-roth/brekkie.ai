import { useRecipeConversationSimulation } from "@/hooks/use-recipe-conversation-simulation";

export function ConversationSimulationTest() {
    const { startSimulation, isRunning, isCompleted } = useRecipeConversationSimulation();

    return (
        <div className="p-4 bg-white rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-4">Conversation Simulation Test</h2>
            <div className="space-y-2">
                <button
                    onClick={startSimulation}
                    disabled={isRunning}
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
                >
                    {isRunning ? "Simulation Running..." : "Start Mediterranean Pasta Conversation"}
                </button>
                {isCompleted && (
                    <p className="text-green-600 font-medium">
                        ✅ Conversation simulation completed! Check the chat for the Mediterranean pasta recipe.
                    </p>
                )}
                {isRunning && (
                    <p className="text-blue-600">
                        🔄 Running conversation simulation...
                    </p>
                )}
            </div>
        </div>
    );
} 