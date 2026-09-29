import React, { useState } from 'react';
import { Rnd } from 'react-rnd';
import './Window.css';

interface WindowProps {
    id: string;
    title: string;
    icon?: React.ReactNode;
    children: React.ReactNode;
    defaultPosition: { x: number; y: number };
    defaultSize: { width: number; height: number };
    onClose?: () => void;
    onMinimize?: () => void;
    resizable?: boolean;
    draggable?: boolean;
    zIndex?: number;
    onFocus?: () => void;
}

export const Window: React.FC<WindowProps> = ({
    id,
    title,
    icon,
    children,
    defaultPosition,
    defaultSize,
    onClose,
    onMinimize,
    resizable = true,
    draggable = true,
    zIndex = 1,
    onFocus,
}) => {
    const [position, setPosition] = useState(defaultPosition);
    const [size, setSize] = useState(defaultSize);

    return (
        <Rnd
            position={position}
            size={size}
            onDragStop={(e, d) => setPosition({ x: d.x, y: d.y })}
            onResizeStop={(e, direction, ref, delta, position) => {
                setSize({
                    width: ref.offsetWidth,
                    height: ref.offsetHeight,
                });
                setPosition(position);
            }}
            enableResizing={resizable}
            disableDragging={!draggable}
            className="terminal-window"
            style={{ zIndex }}
            onMouseDown={onFocus}
            dragHandleClassName="window-titlebar"
            minWidth={300}
            minHeight={200}
        >
            <div className="window-container">
                <div className="window-titlebar">
                    <div className="window-title">
                        {icon && <span className="window-icon">{icon}</span>}
                        <span className="window-title-text">{title}</span>
                    </div>
                    <div className="window-controls">
                        {onMinimize && (
                            <button className="window-control minimize" onClick={onMinimize} aria-label="Minimize">
                                -
                            </button>
                        )}
                        {onClose && (
                            <button className="window-control close" onClick={onClose} aria-label="Close">
                                ×
                            </button>
                        )}
                    </div>
                </div>
                <div className="window-content">{children}</div>
            </div>
        </Rnd>
    );
};
