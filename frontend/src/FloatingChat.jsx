import { useEffect, useRef, useState } from "react";
import {
  Bot,
  Grip,
  MessageCircle,
  X,
} from "lucide-react";

import ChatWidget from "./ChatWidget";


const DEFAULT_WIDTH = 400;
const DEFAULT_HEIGHT = 650;

const MIN_WIDTH = 320;
const MIN_HEIGHT = 420;

const MAX_WIDTH = 900;


export default function FloatingChat({
  externalOpen = false,
  onExternalOpenHandled,
}) {
  const [open, setOpen] = useState(false);

  const [size, setSize] = useState({
    width: DEFAULT_WIDTH,
    height: DEFAULT_HEIGHT,
  });

  const resizeState = useRef(null);


  useEffect(() => {
    if (externalOpen) {
      setOpen(true);
      onExternalOpenHandled?.();
    }
  }, [externalOpen, onExternalOpenHandled]);


  useEffect(() => {
    function handlePointerMove(event) {
      if (!resizeState.current) return;

      const {
        startX,
        startY,
        startWidth,
        startHeight,
      } = resizeState.current;

      /*
       * Widget is anchored bottom-right.
       *
       * Drag LEFT  -> increase width
       * Drag RIGHT -> decrease width
       * Drag UP    -> increase height
       * Drag DOWN  -> decrease height
       */
      const nextWidth =
        startWidth + (startX - event.clientX);

      const nextHeight =
        startHeight + (startY - event.clientY);

      const availableWidth =
        Math.min(
          MAX_WIDTH,
          window.innerWidth - 48
        );

      const availableHeight =
        window.innerHeight - 48;

      setSize({
        width: Math.min(
          availableWidth,
          Math.max(MIN_WIDTH, nextWidth)
        ),

        height: Math.min(
          availableHeight,
          Math.max(MIN_HEIGHT, nextHeight)
        ),
      });
    }


    function handlePointerUp() {
      resizeState.current = null;

      document.body.classList.remove(
        "floating-chat-resizing"
      );
    }


    window.addEventListener(
      "pointermove",
      handlePointerMove
    );

    window.addEventListener(
      "pointerup",
      handlePointerUp
    );


    return () => {
      window.removeEventListener(
        "pointermove",
        handlePointerMove
      );

      window.removeEventListener(
        "pointerup",
        handlePointerUp
      );
    };
  }, []);


  function startResize(event) {
    event.preventDefault();

    resizeState.current = {
      startX: event.clientX,
      startY: event.clientY,
      startWidth: size.width,
      startHeight: size.height,
    };

    document.body.classList.add(
      "floating-chat-resizing"
    );
  }


  return (
    <div className="floating-chat-root">
      {open && (
        <div
          className="floating-chat-panel"
          style={{
            width: `${size.width}px`,
            height: `${size.height}px`,
          }}
        >
          <button
            type="button"
            className="floating-chat-resize-handle"
            onPointerDown={startResize}
            aria-label="Resize chatbot"
            title="Drag to resize chatbot"
          >
            <Grip size={15} />
          </button>


          <div className="floating-chat-topbar">
            <div>
              <span className="floating-chat-icon">
                <Bot size={18} />
              </span>

              <div>
                <strong>Datamart AI</strong>
                <span>Online</span>
              </div>
            </div>

            <button
              type="button"
              className="floating-chat-close"
              onClick={() => setOpen(false)}
              aria-label="Close chatbot"
            >
              <X size={19} />
            </button>
          </div>


          <div className="floating-chat-content">
            <ChatWidget />
          </div>
        </div>
      )}


      {!open && (
        <button
          type="button"
          className="floating-chat-launcher"
          onClick={() => setOpen(true)}
          aria-label="Open Datamart AI Assistant"
        >
          <MessageCircle size={25} />
          <span>Ask Datamart AI</span>
        </button>
      )}
    </div>
  );
}
