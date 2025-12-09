import streamlit as st
from query_rag import build_retrievers, create_rag_chain
from datetime import datetime
import json
import time

# ---------------------------------------------------------
# Backend: build retrievers & RAG chain (unchanged logic)
# ---------------------------------------------------------
retrievers = build_retrievers(include_patient_data=True)
chain_call = create_rag_chain(
    retrievers,
    use_multiquery=True,
    use_rerank=True,
)

# ---------------------------------------------------------
# App-level constants
# ---------------------------------------------------------
APP_TITLE = "Cysterhood"
APP_TAGLINE = "#YOUterusMatters · Evidence-based, patient-friendly PCOS answers"

SAMPLE_QUESTIONS = [
    "What is PCOS and what are the most common symptoms?",
    "How does PCOS affect fertility and periods?",
    "What lifestyle changes can help manage PCOS symptoms?",
]

# ---------------------------------------------------------
# Streamlit page config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Cysterhood",
    page_icon="💜",
    layout="wide",
)

# ---------------------------------------------------------
# Global styles (lavender theme + alignment)
# ---------------------------------------------------------
def inject_global_styles():
    st.markdown(
        """
        <style>
        :root {
            --lavender-bg: #f5efff;
            --lavender-soft: #efe3ff;
            --lavender-strong: #b58bff;
            --lavender-deep: #3a255c;
            --text-muted: #6f5a96;
            --border-subtle: rgba(167, 118, 222, 0.35);
        }

        /* App background */
        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at top left, #f8edff 0, #f3e5ff 38%, #e4d3ff 100%);
            color: var(--lavender-deep);
            /* Prevent auto-scroll on load */
            overflow-x: hidden;
            overflow-y: auto;
        }
        [data-testid="stHeader"] {
            background: transparent;
        }
        
        /* Prevent auto-scroll to bottom on page load */
        html, body {
            scroll-behavior: auto;
        }
        
        /* Ensure page starts at top */
        main {
            scroll-behavior: auto;
        }
        
        /* Prevent chat container from auto-scrolling */
        [data-testid="stChatMessageContainer"] {
            scroll-behavior: auto;
        }
        
        /* Hide scrollbar if content fits viewport */
        [data-testid="stAppViewContainer"]:not(:hover) {
            scrollbar-width: thin;
        }

        /* Center column + bottom padding so chat doesn't go under input */
        /* This container automatically adjusts when Streamlit sidebar opens */
        .block-container {
            max-width: 840px;
            padding-top: 1.5rem;
            padding-bottom: 7.5rem;
            margin: 0 auto;
            /* Streamlit automatically shifts this when sidebar opens, so we don't need to adjust it */
        }
        
        /* Ensure main app container respects sidebar */
        [data-testid="stAppViewContainer"] {
            /* Streamlit handles the main container shift automatically */
            /* We just need to ensure chat input follows the same logic */
        }

        /* Hide default footer */
        footer {visibility: hidden;}
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: #f9f7fc;
        }
        
        [data-testid="stSidebar"] > div {
            background: #f9f7fc;
            padding: 0 !important;
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
        }
        
        /* Sidebar content area */
        [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            padding: 1rem 1rem 1.5rem 1rem !important;
        }
        
        /* Sidebar content wrapper */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0 !important;
            padding-top: 0 !important;
        }
        
        /* Logo - first element, no top margin */
        [data-testid="stSidebar"] [data-testid="stImage"] {
            margin-top: 0 !important;
            padding-top: 0 !important;
            margin-bottom: 1.5rem !important;
        }
        
        /* Remove default margins */
        [data-testid="stSidebar"] .element-container {
            margin-bottom: 0 !important;
            margin-top: 0 !important;
        }
        
        /* Sidebar buttons */
        [data-testid="stSidebar"] button[kind="primary"] {
            display: flex !important;
            flex-direction: row !important;
            justify-content: center !important;
            align-items: center !important;
            padding: 6px 12px !important;
            gap: 8px !important;
            min-width: 64px !important;
            height: 32px !important;
            background: #7B51C8 !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            color: white !important;
            transition: background-color 120ms ease !important;
            margin-bottom: 1.5rem !important;
            flex: none !important;
            align-self: stretch !important;
            flex-grow: 0 !important;
        }
        
        [data-testid="stSidebar"] button[kind="primary"]:hover {
            background: #6C46B1 !important;
        }
        
        /* Section title */
        .sidebar-section-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: #6f5a96;
            margin-bottom: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* Sidebar secondary buttons (chat history) */
        [data-testid="stSidebar"] button[kind="secondary"] {
            background: white !important;
            color: var(--lavender-deep) !important;
            border: 1px solid #e6e0f0 !important;
            border-radius: 8px !important;
            padding: 0.6rem 0.8rem !important;
            text-align: left !important;
            font-size: 0.9rem !important;
            margin-bottom: 0.5rem !important;
            transition: all 120ms ease !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            display: block !important;
        }
        
        [data-testid="stSidebar"] button[kind="secondary"]:hover {
            background: #f5f0ff !important;
            border-color: #c7a7ff !important;
        }
        
        [data-testid="stSidebar"] button[kind="secondary"]:disabled {
            background: #f5f0ff !important;
            border-color: #b58bff !important;
            opacity: 1 !important;
        }
        
        /* No chats text */
        .no-chats-text {
            font-size: 0.85rem;
            color: #9d8bb8;
            font-style: italic;
            padding: 0.5rem 0;
        }
        
        /* Spacer to push About to bottom */
        .sidebar-spacer {
            flex: 1;
            min-height: 2rem;
        }
        
        /* About link at bottom */
        .about-link {
            margin-top: auto;
            padding-top: 1rem;
            border-top: 1px solid #e6e0f0;
            font-size: 0.9rem;
        }
        
        .about-link a {
            color: #7B51C8 !important;
            text-decoration: none !important;
            font-weight: 500 !important;
        }
        
        .about-link a:hover {
            color: #6C46B1 !important;
            text-decoration: underline !important;
        }

        /* Header */
        .cys-header-title {
            font-size: 1.9rem;
            font-weight: 700;
            color: var(--lavender-deep);
            margin-bottom: 0.1rem;
        }
        .cys-header-tagline {
            font-size: 0.95rem;
            color: var(--text-muted);
        }

        /* Empty-state card */
        .cys-empty-card {
            background: rgba(255, 255, 255, 0.96);
            border-radius: 26px;
            padding: 2.6rem 2.3rem 2.1rem 2.3rem;
            border: 1px solid var(--border-subtle);
            box-shadow: 0 18px 46px rgba(74, 32, 115, 0.16);
            text-align: center;
            margin-top: 1rem;
        }
        .cys-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            padding: 0.32rem 0.9rem;
            border-radius: 999px;
            background: rgba(180, 139, 255, 0.12);
            color: #5b358d;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.9rem;
        }
        .cys-empty-card h1 {
            font-size: 2.2rem;
            margin-bottom: 0.35rem;
            color: var(--lavender-deep);
        }
        .cys-empty-card p {
            font-size: 0.98rem;
            color: var(--text-muted);
            margin-bottom: 1.4rem;
        }

        /* Sample question buttons */
        .cys-sample-row {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 0.75rem;
            margin: 0.6rem 0 1.6rem 0;
        }
        .cys-sample-row button {
            border-radius: 999px !important;
            border: 1px solid #c7a7ff !important;
            background: rgba(203, 168, 255, 0.23) !important;
            color: var(--lavender-deep) !important;
            font-size: 0.9rem !important;
            padding: 0.5rem 1.2rem !important;
            white-space: pre-wrap !important;
            transition: transform 120ms ease-out, box-shadow 120ms ease-out,
                        background-color 120ms ease-out;
        }
        .cys-sample-row button:hover {
            background: #cba8ff !important;
            box-shadow: 0 10px 26px rgba(90, 48, 140, 0.25);
            transform: translateY(-1px);
        }

        /* Chat rows: alignment */
        .cys-row {
            display: flex;
            gap: 0.6rem;
            margin: 0.35rem 0;
        }
        .cys-row-assistant {
            justify-content: flex-start;
        }
        .cys-row-user {
            justify-content: flex-end;
        }

        .cys-avatar {
            width: 36px;
            height: 36px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.45rem;
            box-shadow: 0 10px 26px rgba(70, 38, 117, 0.18);
        }
        .cys-avatar-assistant {
            background: #ffffff;
        }
        .cys-avatar-user {
            background: #ffe9ff;
        }

        .cys-msg {
            border-radius: 18px;
            padding: 0.9rem 1rem;
            box-shadow: 0 12px 32px rgba(69, 32, 115, 0.10);
            max-width: 650px;
            animation: cys-fade-in 160ms ease-out;
        }
        .cys-msg-user {
            background: #f6f0ff;
            border: 1px solid rgba(161, 131, 250, 0.55);
            color: var(--lavender-deep);
        }
        .cys-msg-assistant {
            background: #ffffff;
            border: 1px solid rgba(180, 139, 255, 0.45);
        }

        @keyframes cys-fade-in {
            from {
                opacity: 0;
                transform: translateY(6px) scale(0.98);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        /* Thinking indicator bubble */
        .cys-thinking {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }
        .cys-dot {
            width: 6px;
            height: 6px;
            border-radius: 999px;
            background: #b58bff;
            animation: cys-bounce 900ms infinite ease-in-out;
        }
        .cys-dot:nth-child(2) {
            animation-delay: 120ms;
        }
        .cys-dot:nth-child(3) {
            animation-delay: 240ms;
        }
        @keyframes cys-bounce {
            0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
            40% { transform: translateY(-4px); opacity: 1; }
        }
        .cys-thinking-text {
            font-size: 0.9rem;
            color: var(--text-muted);
        }

        /* Chat input fixed at bottom - centered in main content area */
        [data-testid="stChatInput"] {
            position: fixed !important;
            bottom: 20px !important;
            left: 50% !important;
            right: auto !important;
            transform: translateX(-50%) !important;
            width: auto !important;
            min-width: 400px !important;
            max-width: 600px !important;
            padding: 0 !important;
            margin: 0 !important;
            background: transparent !important;
            border: none !important;
            z-index: 10000 !important; /* High z-index to stay above everything */
            box-sizing: border-box !important;
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            /* Smooth transition when sidebar opens/closes */
            transition: left 300ms cubic-bezier(0.4, 0, 0.2, 1), 
                        transform 300ms cubic-bezier(0.4, 0, 0.2, 1),
                        max-width 300ms cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        
        /* Inner container - centered content */
        [data-testid="stChatInput"] > div {
            width: 100% !important;
            max-width: 100% !important;
            margin: 0 auto !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-sizing: border-box !important;
            background: transparent !important;
        }
        
        /* Aggressively remove all borders and backgrounds from ALL children */
        [data-testid="stChatInput"] * {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        
        /* Main input container - ChatGPT-style with rounded corners and shadow */
        [data-testid="stChatInput"] [data-testid="stChatInputTextArea"] {
            background: #FFFFFF !important;
            border: 1.5px solid #CFC8D2 !important;
            border-radius: 16px !important;
            padding: 8px 12px 8px 16px !important;
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            transition: border-color 200ms ease, box-shadow 200ms ease !important;
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            flex: 1 1 auto !important;
            /* ChatGPT-style shadow */
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 
                        0 2px 4px rgba(0, 0, 0, 0.04) !important;
        }
        
        /* Active State - enhanced shadow on focus */
        [data-testid="stChatInput"] [data-testid="stChatInputTextArea"]:focus-within {
            border-color: #7B51C8 !important;
            box-shadow: 0 6px 16px rgba(123, 81, 200, 0.15), 
                        0 2px 6px rgba(123, 81, 200, 0.1) !important;
        }
        /* Textarea */
        [data-testid="stChatInput"] textarea {
            padding: 10px 0 !important;
            min-height: 44px !important;
            max-height: 120px !important;
            font-size: 1rem !important;
            color: var(--lavender-deep) !important;
            outline: none !important;
            flex: 1 !important;
        }
        
        [data-testid="stChatInput"] textarea::placeholder {
            color: #9d8bb8;
        }
        
        /* Send button - override the wildcard for button styling */
        [data-testid="stChatInput"] button[kind="primary"] {
            display: flex !important;
            flex-direction: row !important;
            justify-content: center !important;
            align-items: center !important;
            width: 44px !important;
            height: 36px !important;
            min-width: 44px !important;
            min-height: 36px !important;
            margin: 0 !important;
            padding: 12px !important;
            background: #7B51C8 !important;
            border: none !important;
            border-radius: 8px !important;
            color: #ffffff !important;
            flex-shrink: 0 !important;
            transition: background-color 120ms ease-out !important;
        }
        
        [data-testid="stChatInput"] button[kind="primary"]:hover {
            background: #6C46B1 !important;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-bottom: 7rem;
            }
            [data-testid="stChatInput"] > div {
                padding: 0 1rem;
            }
            
            /* On mobile, sidebar overlays so don't shift content */
            .sidebar-open [data-testid="stChatInput"] > div {
                transform: none !important;
            }
        }
        
        </style>
        
        <script>
        // Center chat input horizontally in main content area
        // Adjusts position and width based on sidebar state to keep it centered
        function adjustChatInputForSidebar() {
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            const chatInput = document.querySelector('[data-testid="stChatInput"]');
            const mainContainer = document.querySelector('[data-testid="stAppViewContainer"]');
            
            if (!chatInput) return;
            
            const isMobile = window.innerWidth <= 768;
            
            if (isMobile) {
                // Mobile: Sidebar overlays, so chat input uses full width with margins
                chatInput.style.left = '50%';
                chatInput.style.right = 'auto';
                chatInput.style.transform = 'translateX(-50%)';
                chatInput.style.width = 'calc(100% - 32px)';
                chatInput.style.minWidth = 'auto';
                chatInput.style.maxWidth = 'calc(100% - 32px)';
                return;
            }
            
            // Desktop: Center within main content area
            if (!sidebar || !mainContainer) {
                // No sidebar: Center in viewport
                chatInput.style.left = '50%';
                chatInput.style.right = 'auto';
                chatInput.style.transform = 'translateX(-50%)';
                chatInput.style.width = 'auto';
                chatInput.style.minWidth = '400px';
                chatInput.style.maxWidth = '600px';
                return;
            }
            
            // Check sidebar state
            const sidebarRect = sidebar.getBoundingClientRect();
            const sidebarComputed = window.getComputedStyle(sidebar);
            const isExpanded = sidebar.getAttribute('aria-expanded') === 'true';
            const sidebarVisible = sidebarRect.width > 0 && sidebarRect.left >= 0 && 
                                  sidebarComputed.display !== 'none' && 
                                  sidebarComputed.visibility !== 'hidden';
            
            // Get main container position to calculate center point
            const mainRect = mainContainer.getBoundingClientRect();
            const viewportWidth = window.innerWidth;
            const sidebarWidth = sidebarVisible && isExpanded ? sidebarRect.width : 0;
            const mainContentLeft = mainRect.left;
            const mainContentRight = mainRect.right;
            const mainContentWidth = mainContentRight - mainContentLeft;
            const mainContentCenter = mainContentLeft + (mainContentWidth / 2);
            
            // Calculate available width for chat input (with margins)
            const sideMargins = 40; // 20px on each side
            const availableWidth = mainContentWidth - sideMargins;
            const maxChatWidth = Math.min(600, Math.max(400, availableWidth));
            
            if (isExpanded && sidebarVisible && sidebarWidth > 0) {
                // Sidebar is open: center within main content area
                chatInput.style.left = mainContentCenter + 'px';
                chatInput.style.right = 'auto';
                chatInput.style.transform = 'translateX(-50%)';
                chatInput.style.width = 'auto';
                chatInput.style.minWidth = '400px';
                chatInput.style.maxWidth = maxChatWidth + 'px';
            } else {
                // Sidebar is closed: center in viewport
                chatInput.style.left = '50%';
                chatInput.style.right = 'auto';
                chatInput.style.transform = 'translateX(-50%)';
                chatInput.style.width = 'auto';
                chatInput.style.minWidth = '400px';
                chatInput.style.maxWidth = '600px';
            }
            
            // Ensure visibility
            chatInput.style.zIndex = '10000';
            chatInput.style.visibility = 'visible';
            chatInput.style.opacity = '1';
        }
        
        // Run immediately and with delays to catch initial render
        adjustChatInputForSidebar();
        setTimeout(adjustChatInputForSidebar, 50);
        setTimeout(adjustChatInputForSidebar, 100);
        setTimeout(adjustChatInputForSidebar, 200);
        setTimeout(adjustChatInputForSidebar, 500);
        setTimeout(adjustChatInputForSidebar, 1000);
        
        // Watch for sidebar changes
        const sidebarObserver = new MutationObserver((mutations) => {
            let shouldAdjust = false;
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes') {
                    if (mutation.attributeName === 'aria-expanded' || 
                        mutation.attributeName === 'style' || 
                        mutation.attributeName === 'class') {
                        shouldAdjust = true;
                    }
                }
            });
            if (shouldAdjust) {
                setTimeout(adjustChatInputForSidebar, 50);
            }
        });
        
        // Observe sidebar for changes
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            sidebarObserver.observe(sidebar, {
                attributes: true,
                attributeFilter: ['aria-expanded', 'style', 'class'],
                childList: false,
                subtree: false
            });
        }
        
        // Watch for window resize and main container changes
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(adjustChatInputForSidebar, 100);
        });
        
        // Watch for chat input and main container creation/updates
        const bodyObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {
                        const testId = node.getAttribute && node.getAttribute('data-testid');
                        if (testId === 'stChatInput' || testId === 'stSidebar' || testId === 'stAppViewContainer') {
                            setTimeout(adjustChatInputForSidebar, 50);
                        }
                    }
                });
            });
        });
        
        bodyObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // Periodic check as backup
        setInterval(adjustChatInputForSidebar, 2000);
        
        // ============================================================
        // Prevent auto-scroll to bottom on page load
        // ============================================================
        
        // Ensure page starts at top on load
        function preventAutoScroll() {
            // Scroll to top immediately
            window.scrollTo({ top: 0, behavior: 'auto' });
            document.documentElement.scrollTop = 0;
            document.body.scrollTop = 0;
            
            // Prevent any chat input auto-focus from scrolling
            const chatInput = document.querySelector('[data-testid="stChatInput"]');
            if (chatInput) {
                // Remove autofocus attribute if present
                const textarea = chatInput.querySelector('textarea');
                if (textarea) {
                    textarea.removeAttribute('autofocus');
                    // Prevent focus from scrolling on initial load
                    const preventFocusScroll = function(e) {
                        if (window.scrollY < 100) {
                            e.preventDefault();
                            textarea.removeEventListener('focus', preventFocusScroll);
                        }
                    };
                    textarea.addEventListener('focus', preventFocusScroll, { once: true });
                }
            }
            
            // Prevent chat message container from auto-scrolling
            const chatContainer = document.querySelector('[data-testid="stChatMessageContainer"]');
            if (chatContainer) {
                chatContainer.scrollTop = 0;
            }
        }
        
        // Run on page load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', preventAutoScroll);
        } else {
            preventAutoScroll();
        }
        
        // Also run after delays to catch any late-loading content
        setTimeout(preventAutoScroll, 100);
        setTimeout(preventAutoScroll, 300);
        setTimeout(preventAutoScroll, 500);
        setTimeout(preventAutoScroll, 1000);
        
        // Prevent scroll on window load
        window.addEventListener('load', function() {
            window.scrollTo({ top: 0, behavior: 'auto' });
            preventAutoScroll();
        }, { once: true });
        
        // Track if user has manually scrolled
        let userHasScrolled = false;
        let initialLoad = true;
        
        window.addEventListener('scroll', function() {
            if (initialLoad && window.scrollY > 50) {
                // If page auto-scrolled on load, scroll back to top
                if (!userHasScrolled) {
                    window.scrollTo({ top: 0, behavior: 'auto' });
                }
            }
            if (window.scrollY > 10) {
                userHasScrolled = true;
                initialLoad = false;
            }
        }, { passive: true });
        
        // Mark initial load complete after a delay
        setTimeout(function() {
            initialLoad = false;
        }, 2000);
        
        // Aggressively style the submit button by modifying inline styles
        function styleSubmitButton() {
            const button = document.querySelector('[data-testid="stChatInputSubmitButton"]');
            if (!button) return;
            
            // Set inline styles directly (this overrides everything)
            button.style.cssText = `
                width: 44px !important;
                height: 36px !important;
                min-width: 44px !important;
                min-height: 36px !important;
                max-width: 44px !important;
                max-height: 36px !important;
                padding: 0 !important;
                margin: 0 !important;
                background: #7B51C8 !important;
                background-color: #7B51C8 !important;
                background-image: none !important;
                border: none !important;
                border-radius: 8px !important;
                flex-shrink: 0 !important;
                transition: background-color 120ms ease !important;
                box-shadow: none !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                cursor: pointer !important;
            `;
            
            // Style the SVG icon
            const svg = button.querySelector('svg');
            if (svg) {
                svg.style.cssText = `
                    width: 16px !important;
                    height: 16px !important;
                    fill: #ffffff !important;
                    color: #ffffff !important;
                `;
            }
            
            // Add hover effect via event listeners
            button.addEventListener('mouseenter', () => {
                button.style.backgroundColor = '#6C46B1';
                button.style.background = '#6C46B1';
            });
            button.addEventListener('mouseleave', () => {
                button.style.backgroundColor = '#7B51C8';
                button.style.background = '#7B51C8';
            });
        }
        
        // Run immediately and repeatedly
        styleSubmitButton();
        setTimeout(styleSubmitButton, 100);
        setTimeout(styleSubmitButton, 500);
        setTimeout(styleSubmitButton, 1000);
        
        // Watch for DOM changes
        const observer = new MutationObserver(() => {
            styleSubmitButton();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // Also run on interval as backup
        setInterval(styleSubmitButton, 2000);
        </script>
        </style>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# Helpers: state, header, views
# ---------------------------------------------------------
def init_state():
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "sample_question" not in st.session_state:
        st.session_state["sample_question"] = None
    if "pending_answer" not in st.session_state:
        st.session_state["pending_answer"] = False
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "current_chat_id" not in st.session_state:
        st.session_state["current_chat_id"] = None


def save_chat_to_history():
    """Save current chat to history when starting a new chat"""
    if st.session_state["messages"] and st.session_state["current_chat_id"]:
        # Get first user message as title
        first_message = next((msg["content"] for msg in st.session_state["messages"] if msg["role"] == "user"), "New Chat")
        title = first_message[:50] + "..." if len(first_message) > 50 else first_message
        
        # Check if this chat already exists in history
        existing_chat = next((chat for chat in st.session_state["chat_history"] if chat["id"] == st.session_state["current_chat_id"]), None)
        
        if existing_chat:
            # Update existing chat
            existing_chat["messages"] = st.session_state["messages"].copy()
            existing_chat["title"] = title
            existing_chat["timestamp"] = datetime.now()
        else:
            # Add new chat to history
            st.session_state["chat_history"].insert(0, {
                "id": st.session_state["current_chat_id"],
                "title": title,
                "messages": st.session_state["messages"].copy(),
                "timestamp": datetime.now()
            })


def start_new_chat():
    """Start a new chat session"""
    save_chat_to_history()
    st.session_state["messages"] = []
    st.session_state["current_chat_id"] = f"chat_{int(time.time() * 1000)}"
    st.session_state["pending_answer"] = False


def load_chat(chat_id):
    """Load a chat from history"""
    save_chat_to_history()
    chat = next((c for c in st.session_state["chat_history"] if c["id"] == chat_id), None)
    if chat:
        st.session_state["messages"] = chat["messages"].copy()
        st.session_state["current_chat_id"] = chat_id
        st.session_state["pending_answer"] = False


def render_sidebar():
    """Render the sidebar with logo, new chat button, and chat history"""
    with st.sidebar:
        # Logo
        st.image("assets/cysterhood_logo.png", width=140)
        
        # New Chat Button
        if st.button("+ New Chat", use_container_width=True, type="primary", key="new_chat_btn"):
            start_new_chat()
            st.rerun()
        
        # Export Chat Button (if there are messages)
        if st.session_state.get("messages"):
            chat_text = format_chat_for_export()
            st.download_button(
                "💾 Export Chat",
                chat_text,
                file_name=f"cysterhood_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
                help="Download conversation as text file",
                key="export_chat_btn"
            )
        
        # Chat History
        st.markdown('<div class="sidebar-section-title">Your Chats</div>', unsafe_allow_html=True)
        
        if st.session_state["chat_history"]:
            for idx, chat in enumerate(st.session_state["chat_history"][:10]):  # Show last 10 chats
                if st.button(
                    chat["title"],
                    key=f"chat_{chat['id']}_{idx}",
                    use_container_width=True,
                    disabled=chat["id"] == st.session_state.get("current_chat_id")
                ):
                    load_chat(chat["id"])
                    st.rerun()
        else:
            st.markdown('<div class="no-chats-text">No previous chats</div>', unsafe_allow_html=True)
        
        # Spacer to push About link to bottom
        st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)
        
        # About link at bottom
        st.markdown('<div class="about-link">ℹ️ <a href="#" target="_self">About Cysterhood</a></div>', unsafe_allow_html=True)


def render_header():
    col_logo, col_text = st.columns([1, 3], gap="small")
    with col_logo:
        # Update this path to where you stored your logo
        st.image("assets/cysterhood_logo.png", width=120)
    with col_text:
        st.markdown(
            f"<div class='cys-header-title'>{APP_TITLE}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='cys-header-tagline'>{APP_TAGLINE}</div>",
            unsafe_allow_html=True,
        )


def render_empty_state():
    with st.container():
        
        st.markdown(
            "<h1>Hi! How can I support you today?</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p>Welcome to Cysterhood - a safe haven for girls to openly discuss PCOS/PCOD."
            "Ask your questions below and get research-backed, patient-friendly answers.</p>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div style='font-weight:600; margin-top:0.8rem;'>Try asking…</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<div class='cys-sample-row'>", unsafe_allow_html=True)
        sample_cols = st.columns(len(SAMPLE_QUESTIONS))
        for idx, (col, q) in enumerate(zip(sample_cols, SAMPLE_QUESTIONS)):
            with col:
                if st.button(q, key=f"sample-{idx}"):
                    st.session_state["sample_question"] = q
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            "<p style='font-size:0.83rem; color:#7d689d; margin-top:1.1rem;'>"
            "Cysterhood is for education only and does not replace professional "
            "medical advice. Please consult your doctor for personalised care."
            "</p>",
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)


def build_message_html(role: str, content: str) -> str:
    """Return HTML for a left/right aligned message row."""
    if role == "user":
        # Right aligned
        return f"""
        <div class="cys-row cys-row-user">
            <div class="cys-msg cys-msg-user">
                {content}
            </div>
            <div class="cys-avatar cys-avatar-user">🧑‍🦰</div>
        </div>
        """
    else:
        # Assistant, left aligned
        # Add copy button below assistant message
        import json
        import html
        # Escape content for JavaScript - use JSON encoding which handles all special chars
        escaped_content_js = json.dumps(content)
        # Escape content for HTML display
        escaped_content_html = html.escape(content)
        # Generate unique ID for this button
        import hashlib
        button_id = f"copy-btn-{hashlib.md5(content.encode()).hexdigest()[:8]}"
        copy_button_html = f"""
        <div style="text-align: right; margin-top: 0.5rem;">
            <button 
                id="{button_id}"
                data-content={escaped_content_js}
                onclick="(function(){{const btn=document.getElementById('{button_id}');const text=JSON.parse(btn.getAttribute('data-content'));navigator.clipboard.writeText(text).then(()=>{{btn.textContent='✓ Copied!';setTimeout(()=>{{btn.textContent='📋 Copy Answer';}},2000);}}).catch(()=>alert('Failed to copy'));}})()" 
                style="
                    background-color: #f0e2ff; 
                    color: #5b358d; 
                    border: 1px solid #c7a7ff; 
                    padding: 0.3rem 0.8rem; 
                    border-radius: 8px; 
                    font-size: 0.8rem; 
                    cursor: pointer;
                    transition: background-color 0.2s ease;
                "
                onmouseover="this.style.backgroundColor='#e4d3ff'"
                onmouseout="this.style.backgroundColor='#f0e2ff'"
            >
                📋 Copy Answer
            </button>
        </div>
        """
        return f"""
        <div class="cys-row cys-row-assistant">
            <div class="cys-avatar cys-avatar-assistant">🤖</div>
            <div class="cys-msg cys-msg-assistant">
                {escaped_content_html}
                {copy_button_html}
            </div>
        </div>
        """


def build_thinking_html() -> str:
    """Animated 'thinking…' bubble for the assistant."""
    return """
    <div class="cys-row cys-row-assistant">
        <div class="cys-avatar cys-avatar-assistant">🤖</div>
        <div class="cys-msg cys-msg-assistant cys-thinking">
            <span class="cys-dot"></span>
            <span class="cys-dot"></span>
            <span class="cys-dot"></span>
            <span class="cys-thinking-text">Thinking…</span>
        </div>
    </div>
    """


def render_chat_history():
    """Render all previous messages in session_state."""
    for msg in st.session_state["messages"]:
        html = build_message_html(msg["role"], msg["content"])
        st.markdown(html, unsafe_allow_html=True)


def format_chat_for_export():
    """Format chat history for export as text file."""
    lines = [f"Cysterhood Chat Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"]
    lines.append("=" * 60 + "\n\n")
    
    for msg in st.session_state.get("messages", []):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        lines.append(f"{role.upper()}: {content}\n")
        lines.append("-" * 60 + "\n")
    
    return "\n".join(lines)


def build_answer_with_sources(answer, docs):
    """Compose markdown block combining answer with compact sources list."""
    lines = [answer]
    if docs:
        # Count unique sources
        unique_titles = set()
        for doc in docs:
            meta = doc.metadata if hasattr(doc, 'metadata') else {}
            title = meta.get("title", "N/A")
            if title != "N/A":
                unique_titles.add(title)
        source_count = len(unique_titles)
        
        lines.append("\n---\n**Sources**")
        if source_count > 0:
            lines.append(f"*Found {source_count} source{'s' if source_count > 1 else ''}*")
        # Deduplicate sources by title to avoid showing same paper multiple times
        seen_titles = set()
        unique_docs = []
        for doc in docs:
            meta = doc.metadata if hasattr(doc, 'metadata') else {}
            title = meta.get("title", "N/A")
            # Only add if we haven't seen this title before
            if title not in seen_titles and title != "N/A":
                seen_titles.add(title)
                unique_docs.append(doc)
        
        # Display up to 3 unique sources
        for i, doc in enumerate(unique_docs[:3]):
            meta = doc.metadata if hasattr(doc, 'metadata') else {}
            title = meta.get("title", "N/A")
            year = meta.get("year", "N/A")
            url = meta.get("url", None)
            pmid = meta.get("pmid", None)
            source_type = meta.get("source", "Research")
            
            snippet = (doc.page_content or "").strip().replace("\n", " ") if hasattr(doc, 'page_content') else ""
            if len(snippet) > 260:
                snippet = snippet[:260].rstrip() + "..."
            
            # Build title with clickable link if URL or PMID is available
            # Check if url exists and is valid
            if url and str(url).strip() and str(url).strip().lower() not in ["none", "nan", ""]:
                title_link = f"[{title}]({url})"
            elif pmid and str(pmid).strip() and str(pmid).strip().lower() not in ["none", "nan", ""]:
                title_link = f"[{title}](https://pubmed.ncbi.nlm.nih.gov/{pmid})"
            else:
                title_link = title
            
            # Build the source line
            source_line = f"**{i+1}. {title_link}**"
            if year != "N/A":
                source_line += f" ({year})"
            if source_type:
                source_line += f" • {source_type}"
            
            lines.append(
                f"{source_line}  \n"
                f"> {snippet}"
            )
    return "\n\n".join(lines)

# ---------------------------------------------------------
# Main app flow
# ---------------------------------------------------------
def main():
    inject_global_styles()
    init_state()
    
    # Initialize chat ID if this is a new session
    if st.session_state["current_chat_id"] is None:
        st.session_state["current_chat_id"] = f"chat_{int(time.time() * 1000)}"
    
    # Render sidebar
    render_sidebar()

    render_header()
    st.markdown("")  # spacer

    # 1) Render either empty state or existing history
    if not st.session_state["messages"]:
        render_empty_state()
    else:
        render_chat_history()

    # 2) Handle new user input (typed or sample) -> store & rerun immediately
    pending_sample = st.session_state.get("sample_question")
    user_text = st.chat_input("Ask a question about PCOS…")

    # Sample question was clicked earlier
    if pending_sample:
        new_question = pending_sample
        st.session_state["sample_question"] = None
        st.session_state["messages"].append({"role": "user", "content": new_question})
        st.session_state["pending_answer"] = True
        st.rerun()

    # User typed a new question
    if user_text:
        new_question = user_text
        st.session_state["messages"].append({"role": "user", "content": new_question})
        st.session_state["pending_answer"] = True
        st.rerun()

    # 3) If we have a pending answer, generate it (user message is already shown)
    if (
        st.session_state.get("pending_answer")
        and st.session_state["messages"]
        and st.session_state["messages"][-1]["role"] == "user"
    ):
        last_user_question = st.session_state["messages"][-1]["content"]

        # Show thinking indicator
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown(build_thinking_html(), unsafe_allow_html=True)

        # Call RAG chain (same functionality as before)
        answer, docs = chain_call(last_user_question, history=[])
        full_reply = build_answer_with_sources(answer, docs)

        # Replace thinking bubble with final answer
        assistant_html = build_message_html("assistant", full_reply)
        thinking_placeholder.markdown(assistant_html, unsafe_allow_html=True)

        # Save assistant message
        st.session_state["messages"].append(
            {"role": "assistant", "content": full_reply}
        )
        st.session_state["pending_answer"] = False
        
        # Update chat history
        save_chat_to_history()


if __name__ == "__main__":
    main()
