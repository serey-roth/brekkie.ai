import { ChevronRight } from 'lucide-react';
import { useState, useRef, useEffect, type ReactNode } from 'react';
import { createPortal } from 'react-dom';

interface MenuItem {
    label: string;
    icon?: ReactNode;
    onClick?: () => void;
    href?: string;
    submenu?: MenuItem[];
    disabled?: boolean;
}

interface MenuProps {
    trigger: ReactNode;
    items: MenuItem[];
    placement?: 'top' | 'bottom' | 'left' | 'right';
    align?: 'start' | 'center' | 'end';
    containerClassName?: string;
    triggerClassName?: string;
    menuClassName?: string;
    offset?: number;
    submenuClassName?: string;
    onOpenChange?: (open: boolean) => void;
}

export function Menu({
    trigger,
    items,
    placement = 'bottom',
    align = 'center',
    containerClassName = '',
    triggerClassName = '',
    menuClassName = '',
    submenuClassName = '',
    offset = 8,
    onOpenChange,
}: MenuProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [position, setPosition] = useState({ top: 0, left: 0 });
    const [activeSubmenu, setActiveSubmenu] = useState<string | null>(null);
    const triggerRef = useRef<HTMLDivElement>(null);
    const menuRef = useRef<HTMLDivElement>(null);

    const handleToggle = () => {
        const newOpen = !isOpen;
        setIsOpen(newOpen);
        setActiveSubmenu(null);
        onOpenChange?.(newOpen);
    };

    const handleItemClick = (item: MenuItem) => {
        if (item.onClick) {
            item.onClick();
        }
        setIsOpen(false);
        setActiveSubmenu(null);
        onOpenChange?.(false);
    };

    const handleItemHover = (item: MenuItem) => {
        if (item.submenu) {
            setActiveSubmenu(item.label);
        }
    };

    const handleItemLeave = () => {
        setActiveSubmenu(null);
    };

    // Close when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (
                triggerRef.current &&
                !triggerRef.current.contains(event.target as Node) &&
                menuRef.current &&
                !menuRef.current.contains(event.target as Node)
            ) {
                setIsOpen(false);
                setActiveSubmenu(null);
                onOpenChange?.(false);
            }
        };

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen, onOpenChange]);

    // Calculate position
    useEffect(() => {
        if (isOpen && triggerRef.current && menuRef.current) {
            const triggerRect = triggerRef.current.getBoundingClientRect();
            const menuRect = menuRef.current.getBoundingClientRect();

            let top = 0;
            let left = 0;

            switch (placement) {
                case 'top':
                    top = triggerRect.top - menuRect.height - offset;
                    break;
                case 'bottom':
                    top = triggerRect.bottom + offset;
                    break;
                case 'left':
                    left = triggerRect.left - menuRect.width - offset;
                    top = triggerRect.top;
                    break;
                case 'right':
                    left = triggerRect.right + offset;
                    top = triggerRect.top;
                    break;
            }

            switch (align) {
                case 'start':
                    left = triggerRect.left;
                    break;
                case 'center':
                    if (placement === 'top' || placement === 'bottom') {
                        left = triggerRect.left + (triggerRect.width - menuRect.width) / 2;
                    }
                    break;
                case 'end':
                    if (placement === 'top' || placement === 'bottom') {
                        left = triggerRect.right - menuRect.width;
                    }
                    break;
            }

            setPosition({ top, left });
        }
    }, [isOpen, placement, align, offset]);

    const renderMenuItem = (item: MenuItem, index: number) => {
        const hasSubmenu = item.submenu && item.submenu.length > 0;
        const isSubmenuOpen = activeSubmenu === item.label;
        const isClickable = item.onClick || hasSubmenu;

        if (!isClickable) {
            return (
                <div key={index} className="text-contrast-subtle px-3 py-2 text-sm">
                    <div className="flex items-center gap-2">
                        {item.icon && <span className="text-contrast-subtle">{item.icon}</span>}
                        <span>{item.label}</span>
                    </div>
                </div>
            );
        }

        return (
            <div
                key={index}
                className="relative"
                onMouseEnter={() => handleItemHover(item)}
                onMouseLeave={handleItemLeave}
            >
                <button
                    onClick={() => handleItemClick(item)}
                    disabled={item.disabled}
                    className="text-contrast hover:bg-primary/5 hover:text-primary flex w-full items-center justify-between px-3 py-2 text-left text-sm transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    <div className="flex items-center gap-2">
                        {item.icon && <span className="text-contrast-subtle">{item.icon}</span>}
                        <span>{item.label}</span>
                    </div>
                    {hasSubmenu && (
                        <ChevronRight
                            size={14}
                            className={`text-contrast-subtle transition-transform duration-150 ${
                                isSubmenuOpen ? 'rotate-90' : ''
                            }`}
                        />
                    )}
                </button>
                {hasSubmenu && isSubmenuOpen && (
                    <div
                        className={`bg-background-light border-border absolute top-0 left-full z-10 min-w-[160px] rounded-lg border shadow-lg backdrop-blur-sm ${submenuClassName}`}
                    >
                        {item.submenu!.map((subItem, subIndex) => (
                            <button
                                key={subIndex}
                                onClick={() => {
                                    if (subItem.onClick) {
                                        subItem.onClick();
                                    }
                                    setIsOpen(false);
                                    setActiveSubmenu(null);
                                    onOpenChange?.(false);
                                }}
                                className="text-contrast hover:bg-primary/5 hover:text-primary flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors duration-150"
                            >
                                {subItem.icon && (
                                    <span className="text-contrast-subtle">{subItem.icon}</span>
                                )}
                                <span>{subItem.label}</span>
                            </button>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className={`relative ${containerClassName}`}>
            <div ref={triggerRef} onClick={handleToggle} className={`${triggerClassName}`}>
                {trigger}
            </div>

            {isOpen &&
                createPortal(
                    <div
                        ref={menuRef}
                        className={`border-border fixed z-50 min-w-[200px] rounded-lg border shadow-xl backdrop-blur-sm ${menuClassName}`}
                        style={{
                            top: position.top,
                            left: position.left,
                            opacity: position.top === 0 && position.left === 0 ? 0 : 1,
                        }}
                    >
                        <div className="py-1">
                            {items.map((item, index) => renderMenuItem(item, index))}
                        </div>
                    </div>,
                    document.body,
                )}
        </div>
    );
}
