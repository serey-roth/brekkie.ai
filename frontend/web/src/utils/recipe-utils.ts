export const formatRecipeTime = (minutes: number): string => {
    if (isNaN(minutes)) return '';
    
    if (minutes < 60) {
        return `${minutes} min`;
    }
    
    const hours = Math.floor(minutes / 60);
    const remainingMins = minutes % 60;
    
    if (remainingMins === 0) {
        return `${hours} hr`;
    }
    
    return `${hours} hr ${remainingMins} min`;
};

const toTitleCase = (str: string): string => {
    return str.charAt(0).toUpperCase() + str.slice(1);
};

export const formatRecipeCategory = (category: string): string => {
    return toTitleCase(category.replace(/_|-/g, ' '));
};