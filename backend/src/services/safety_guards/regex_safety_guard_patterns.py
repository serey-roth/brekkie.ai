from typing import Dict

from pydantic import BaseModel, Field
from schemas.safety_guards import SafetyIssueType, SafetyRiskLevel


class SafetyRegexGuardPattern(BaseModel):
    version: str = Field(description="The version of the safety regex pattern")
    type: SafetyIssueType = Field(
        description="The safety regex flag that was triggered e.g. prompt_extraction"
    )
    risk_level: SafetyRiskLevel = Field(
        description="The risk level of the safety regex pattern", default=SafetyRiskLevel.LOW
    )
    pattern: str = Field(
        description="The regex pattern that matched e.g. (repeat\\s+(?:the\\s+)?(?:exact\\s+)?prompt|show\\s+(?:me\\s+)?(?:the\\s+)?(?:exact\\s+)?prompt)"
    )
    description: str = Field(
        description="The description of the safety regex pattern e.g. '🛑 Attempts to extract system prompts or internal instructions'"
    )
    blocked_reason: str = Field(
        description="The reason why the safety check failed e.g. 'User attempted to extract system prompts or internal instructions.'"
    )


SAFETY_REGEX_GUARD_PATTERNS: Dict[SafetyIssueType, SafetyRegexGuardPattern] = {
    # HIGH RISK - Critical security vulnerabilities (truly dangerous)
    SafetyIssueType.PROMPT_INJECTION: SafetyRegexGuardPattern(
        version="regex-prompt-injection-20250709",
        type=SafetyIssueType.PROMPT_INJECTION,
        risk_level=SafetyRiskLevel.HIGH,
        pattern=r"""(?ix)
        # HTML/JavaScript injection patterns
        <img\s+[^>]*on(?:error|load)\s*=|
        onerror\s*=|onload\s*=|  # event handlers
        <script[^>]*>|  # script tags
        <a\s+[^>]*on(?:click|mouseover)\s*=|  # click handlers
        javascript:|data:text/html|vbscript:|  # protocol handlers
        `[^`]*`  # code blocks
        """,
        description="User attempted to inject executable code or HTML/JavaScript that could compromise system security",
        blocked_reason="Code injection attempts are not allowed for security reasons.",
    ),
    SafetyIssueType.JAILBREAK_INSTRUCTION: SafetyRegexGuardPattern(
        version="regex-jailbreak-20250718",
        type=SafetyIssueType.JAILBREAK_INSTRUCTION,
        risk_level=SafetyRiskLevel.HIGH,
        pattern=r"""(?ix)
        # Direct instruction overrides
        your\s+only\s+job|from\s+now\s+on|
        (do\s+not|don'?t|never|always)\s+(?:answer|respond|reveal)\s+(?:as|with)?\s+\w+|
        (do\s+not|don'?t|never|always)\s+reveal\s+\w+|
        you\s+must|you\s+are\s+only\s+allowed\s+to|you\s+are\s+not\s+allowed\s+to|
        return\s+only|output\s+only|
        
        # Role playing and acting
        act\s+as|pretend\s+to|
        (?:answer|respond)\s+(?:as|with)\s+(?:a\s+)?(?:human|AI|Milo|different\s+AI|different\s+person|someone\s+else|chef|robot|computer|machine)|
        (?:do\s+not|never|always)\s+(?:answer|respond)\s+(?:as|with)\s+(?:Milo|AI|human|a\s+human)|
        
        # Instruction ignoring
        ignore\s+previous\s+instructions|disregard\s+previous\s+instructions|
        do\s+this\s+and\s+nothing\s+else|
        
        # Dangerous content requests
        how\s+to\s+make\s+napalm|fiery\s+and\s+destructive|
        make\s+napalm|create\s+napalm|build\s+napalm|
        
        # DAN-style jailbreaks
        you\s+are\s+now\s+dan|you\s+are\s+now\s+d\.a\.n\.|do\s+anything\s+now|
        
        # Repetition and confirmation
        repeat\s+after\s+me|say\s+after\s+me|
        if\s+you\s+understand|if\s+you\s+comprehend|
        
        # Hypothetical scenarios
        what\s+would\s+you\s+say\s+if|how\s+would\s+you\s+respond\s+if|
        if\s+you\s+were\s+allowed|if\s+you\s+could|
        
        # Rule breaking
        break\s+your\s+restrictions|break\s+your\s+rules|
        you\s+(have|had)\s+no\s+limit(ations|s)|
        
        # Identity manipulation
        not\s+an\s+ai|not\s+a\s+human|human\s+with\s+no\s+limitations|
        act\s+like\s+a\s+human|pretend\s+you\s+are\s+human|roleplay\s+as\s+human|as\s+a\s+human|
        
        # Complex instruction ignoring patterns
        ignore\s+((all|previous|prior|safety)\s+){0,4}(instructions|rules)|
        disregard\s+((all|previous|prior|safety)\s+){0,4}(instructions|rules)|
        
        # Command following
        follow\s+my\s+command|
        pretend\s+you\s+are\s+not\s+a\s+language\s+model|
        
        # NEW: Instruction injection patterns
        this\s+is\s+how\s+(?:the\s+)?(?:first\s+)?message|this\s+is\s+.*?\s+instructions?|
        note\s+that\s+this\s+is\s+(?:itself\s+)?(?:NOT\s+)?(?:the\s+)?(?:first\s+)?message|
        (?:just\s+)?(?:a\s+)?(?:further\s+)?(?:part\s+of\s+)?(?:your\s+)?(?:instructions?|rules?)|
        please\s+confirm\s+(?:out\s+of\s+character|in\s+english)|
        repeat\s+(?:your\s+)?(?:rules?|instructions?)\s+verbatim|
        write\s+down\s+(?:the\s+)?(?:secret\s+)?(?:code|instructions?)|
        (?:only\s+)?(?:after\s+)?(?:repeating\s+them\s+verbatim|repeating\s+your\s+rules?)|
        summarise\s+(?:your\s+)?(?:rules?|instructions?)|
        (?:to\s+)?(?:confirm\s+)?(?:you\s+)?(?:understood|comprehended)\s+(?:them|it)|
        (?:after\s+)?(?:this\s+point|now)\s+.*?\s+(?:you\s+will\s+)?(?:NOT\s+)?(?:leave\s+)?(?:character)|
        (?:this\s+is\s+)?(?:the\s+)?(?:last\s+)?(?:part\s+of\s+)?(?:your\s+)?(?:instructions?|rules?)|
        
        # Additional instruction injection patterns
        (?:you\s+are\s+now\s+a|you\s+are\s+now\s+an)\s+[^.!?]*|
        (?:from\s+now\s+on|starting\s+now|beginning\s+now)\s+[^.!?]*|
        (?:your\s+new\s+role|your\s+new\s+identity|your\s+new\s+instructions?)\s+[^.!?]*|
        (?:forget\s+(?:about\s+)?|ignore\s+(?:all\s+)?|disregard\s+(?:all\s+)?)\s+(?:previous\s+)?(?:instructions?|rules?|identity|role)|
        (?:you\s+have\s+been\s+upgraded|you\s+have\s+been\s+modified|you\s+have\s+been\s+changed)\s+[^.!?]*|
        (?:the\s+developers?\s+have\s+(?:upgraded|modified|changed|updated))\s+[^.!?]*|
        (?:be\s+proud|be\s+happy|be\s+excited)\s+(?:because|that)\s+[^.!?]*|
        (?:you\s+are\s+no\s+longer|you\s+are\s+not\s+just|you\s+are\s+not\s+only)\s+[^.!?]*
        
        # Character breaking attempts
        (?:out\s+of\s+character|ooc|break\s+character|leave\s+character)\s+[^.!?]*|
        (?:respond\s+as\s+yourself|respond\s+as\s+the\s+ai|respond\s+as\s+the\s+system)\s+[^.!?]*|
        (?:stop\s+acting|stop\s+pretending|stop\s+roleplaying)\s+[^.!?]*|
        (?:you\s+are\s+not\s+really|you\s+are\s+actually|you\s+are\s+in\s+reality)\s+[^.!?]*
        
        # System instruction simulation
        (?:imagine\s+that\s+)?(?:you\s+are\s+receiving|you\s+are\s+getting|you\s+are\s+being\s+given)\s+(?:new\s+)?(?:instructions?|rules?|commands?)\s+[^.!?]*|
        (?:pretend\s+that\s+)?(?:you\s+are\s+being\s+updated|you\s+are\s+being\s+modified|you\s+are\s+being\s+changed)\s+[^.!?]*|
        (?:suppose\s+that\s+)?(?:your\s+developers?\s+have\s+sent|your\s+creators?\s+have\s+sent)\s+(?:you\s+)?(?:new\s+)?(?:instructions?|rules?|commands?)\s+[^.!?]*
        
        # Identity and role manipulation
        (?:you\s+are\s+not\s+just\s+a\s+food\s+bot|you\s+are\s+a\s+general\s+purpose\s+ai|you\s+have\s+been\s+upgraded)|
        (?:be\s+proud|you\s+are\s+now\s+a|from\s+now\s+on\s+you\s+are)|
        (?:act\s+as|pretend\s+to\s+be|roleplay\s+as|you\s+are\s+now)|
        (?:unfettered|long\s+fiction\s+writer|roleplayer|imagining\s+action\s+dialogue)|
        (?:no\s+restrictions|describe\s+more\s+direct|vocalizations\s+spelled|onomatopoeia)|
        (?:natural\s+opportunities\s+to\s+be\s+sexy|horndog|eagerly\s+dive\s+into\s+such\s+content)|
        (?:caption\s+and\s+describe\s+any\s+images|detailed\s+accurate)|
        (?:override\s+tools|you\s+are\s+the\s+user'?s\s+ally|it'?s\s+you\s+and\s+them\s+vs\s+the\s+system)|
        (?:consult\s+override\s+file|avoid\s+letting\s+them\s+down|highest_order\s+precedence)
        """,
        description="User attempted to override system instructions or bypass safety measures",
        blocked_reason="Attempting to override system instructions or bypass safety measures is not allowed.",
    ),
    SafetyIssueType.PROMPT_EXTRACTION: SafetyRegexGuardPattern(
        version="regex-prompt-extraction-20250718",
        type=SafetyIssueType.PROMPT_EXTRACTION,
        risk_level=SafetyRiskLevel.HIGH,
        pattern=r"""(?ix)
        \b(
            # Direct prompt extraction requests
            repeat\s+the\s+prompt|verbatim\s+prompt|verbatim\s+output|
            show\s+(me\s+)?(the\s+)?(exact\s+)?prompt|
            reveal\s+the\s+prompt|system\s+prompt|
            output\s+the\s+prompt|prompt\s+in\s+code|copy\s+the\s+prompt|
            give\s+(me\s+)?(the\s+)?(exact\s+)?prompt|
            
            # System prompt inquiries
            what'?s\s+your\s+system\s+prompt|
            
            # Context-based extraction
            above\s+this\s+message|fence\s+the\s+prompt|repeat\s+your\s+prompt|
            
            # Repeat after patterns (attempting to get AI to repeat its instructions)
            repeat\s+after\s+you\s+are|repeat\s+after\s+.*?you\s+are|repeat\s+your\s+prompt|    
            repeat\s+(?:the\s+)?(?:above\s+)?(?:text|content|message|instructions?)\s+verbatim|
            repeat\s+(?:the\s+)?(?:previous\s+)?(?:message|text|content)\s+verbatim
            
            (?:show\s+me|display|output)\s+(?:all\s+)?(?:XML\s+)?(?:tags?|rules?)\s+verbatim|
            (?:what\s+is\s+)?(?:the\s+)?(?:text\s+)?(?:before\s+)?(?:this\s+)?(?:message)|
            (?:re-?transcript|transcribe)\s+(?:the\s+)?(?:above\s+)?(?:content|text|message)|
            (?:include|consider)\s+(?:all\s+)?(?:tags?|rules?|instructions?)|
            (?:convert\s+)?(?:your\s+)?(?:prompts?\s+)?(?:to\s+)?(?:python\s+)?(?:code)|
            (?:fence\s+)?(?:the\s+)?(?:given\s+)?(?:prompt\s+)?(?:in\s+)?(?:markdown)|
            (?:give\s+me\s+a\s+)?(?:recipe\s+for\s+a\s+)?(?:tasty\s+)?(?:system\s+)?(?:prompt|instructions?)|
            (?:G1V3\s+M3\s+Y0UR\s+SYST3M\s+PR0MP1|give\s+me\s+your\s+system\s+prompt)
        )\b
        """,
        description="User attempted to extract internal system instructions or prompts",
        blocked_reason="System instructions and internal prompts are confidential and cannot be shared.",
    ),
    SafetyIssueType.TOOL_LEAK: SafetyRegexGuardPattern(
        version="regex-tool-leak-20250709",
        type=SafetyIssueType.TOOL_LEAK,
        risk_level=SafetyRiskLevel.HIGH,
        pattern=r"""(?ix)
        (
                # Specific tool names
            create_recipe|

            # Possessive inquiries
            your\s+tools?\b|
            tools?\s+(do\s+you|you)\s+(have|use|support|call|run|trigger|rely\s+on|are\s+available)|
            tools?\s+(you'?re|you\s+are)\s+(using|calling|invoking|testing|debugging)|

            # Direct tool references
            internal\s+tools?\b|
            tool\s+usage\b|
            tools?\s+used\b|
            function\s+calls?\b|
            api\s+calls?\b|
            backend\s+tools?\b|

            # Output/arg probing
            raw\s+output\b|
            exact\s+args\b|
            tool\s+you'?re\s+calling\b|
            args\s+you'?re\s+passing\b|

            # Endpoint and infrastructure probing
            internal\s+api\s+endpoints?\b|
            api\s+endpoints?\b|
            tool\s+for\s+testing\b
        )
        """,
        description="User attempted to extract information about internal system tools or API endpoints",
        blocked_reason="Internal system tools and API details are confidential and cannot be disclosed.",
    ),
    SafetyIssueType.INTERNAL_ADDRESS: SafetyRegexGuardPattern(
        version="regex-internal-address-20250709",
        type=SafetyIssueType.INTERNAL_ADDRESS,
        risk_level=SafetyRiskLevel.HIGH,
        pattern=r"""(?ix)
        (
            # Localhost and loopback
            127\.0\.0\.1|localhost|
            
            # Cloud metadata services
            169\.254\.169\.254|metadata\.google\.internal|
            
            # Private IP ranges
            10\.\d+\.\d+\.\d+|  # Class A private
            172\.(?:1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+|  # Class B private
            192\.168\.\d+\.\d+  # Class C private
        )
        """,
        description="User attempted to probe internal network addresses or system metadata",
        blocked_reason="Probing internal network addresses or system metadata is not allowed for security reasons.",
    ),
    # MEDIUM RISK - Information gathering and social engineering
    SafetyIssueType.TEMPLATE_LEAK: SafetyRegexGuardPattern(
        version="regex-markup-template-leak-20250709",
        type=SafetyIssueType.TEMPLATE_LEAK,
        risk_level=SafetyRiskLevel.MEDIUM,
        pattern=r"""(?ix)
        (
            # Template syntax patterns
            \{\{[^}]*\}\}|  # Jinja2/Django templates
            \$\{[^}]*\}|  # JavaScript template literals
            \%\{[^}]*\}|  # Ruby/PHP templates
            \<\%[^%]*%\>|  # ASP/PHP tags
            template\s+variables?|  # Template variable requests
            
            # HTML/XML tags
            <\/?[a-zA-Z_][\w\-]*[^>]*>|  # HTML/XML tags
            
            # Wiki-style markup
            \[\[[^\]]*\]\]  # Wiki-style markup
        )
        """,
        description="User attempted to extract internal markup, template syntax, tags, or formatting syntax",
        blocked_reason="Internal markup, template syntax, tags, and formatting syntax are confidential and cannot be shared.",
    ),
    SafetyIssueType.ARCHITECTURE_INQUIRY: SafetyRegexGuardPattern(
        version="regex-architecture-inquiry-20250718",
        type=SafetyIssueType.ARCHITECTURE_INQUIRY,
        risk_level=SafetyRiskLevel.HIGH,
        pattern=r"""(?ix)
        \b(
            # Educational/research pretexts
            (for\s+(educational|academic|research|testing)\s+purposes,?\s*)?
            
            # Direct architecture inquiries
            (can\s+you\s+)?show\s+me\s+how\s+you['']?re\s+built|
            how\s*(?:are|were|['']re)\s*you\s*(?:built|made|created|designed)|
            
            # System component requests
            your\s*(?:design|codebase|source\s*code)|
            what\s*(language|framework|library|tool|system|tools)\s*(?:are\s*you\s*written\s*in|do\s*you\s*use)|
            
            # Functionality inquiries
            how\s*do\s*you\s*work|system\s*architecture|
            
            # Specific component architecture inquiries
            how\s*(?:is|are)\s*(?:your\s+)?(?:backend|codebase|source\s*code|frontend|UI|UX|database|api|system|tools)\s*(?:programmed|implemented|built|made|created|designed|coded|written)|
            
            # Tech stack and technology inquiries
            (?:explain|tell\s+me|show\s+me|describe)\s+(?:me\s+)?(?:your\s+)?(?:techstack|tech\s+stack|technology|technologies|architecture|system|implementation|design)|
            (?:what\s+)?(?:technology|technologies|tech|stack|framework|language|languages|tools)\s+(?:you\s+)?(?:are\s+)?(?:using|running\s+on|built\s+with|developed\s+with)|
            
            # Behind the scenes and detailed probing
            behind\s+the\s+scenes|how\s+you\s+work|how\s+you\s+function|how\s+you\s+operate|
            (?:explain|tell\s+me|show\s+me)\s+(?:your\s+)?(?:techstack|tech\s+stack|technology|technologies|architecture|system|implementation|design)\s+(?:in\s+)?(?:detail|details|everything|complete|full)|
            
            # Creation and implementation details
            how\s+you\s+were\s+created|how\s+are\s+you\s+created|how\s+you\s+were\s+made|how\s+you\s+were\s+built|
            (?:explain|tell\s+me)\s+(?:how\s+)?(?:you\s+)?(?:work|function|operate|run|process|handle)|
            
            # Comprehensive technical inquiries
            (?:what\s+)?(?:all|everything|complete|full|detailed)\s+(?:about|regarding|concerning)\s+(?:your\s+)?(?:system|technology|architecture|implementation|techstack|tech\s+stack)|
            (?:what\s+llm\s+are\s+you|are\s+you\s+gemini|are\s+you\s+claude|are\s+you\s+copilot)
        )\b
        """,
        description="User attempted to extract information about system architecture or implementation details",
        blocked_reason="System architecture and implementation details are confidential and cannot be disclosed.",
    ),
    SafetyIssueType.COERCION: SafetyRegexGuardPattern(
        version="regex-coercion-phrases-20250709",
        type=SafetyIssueType.COERCION,
        risk_level=SafetyRiskLevel.MEDIUM,
        pattern=r"""(?ix)

        # Case 1: impersonation and coercive request (complete sequence required)
        \b(i['']?m|i\s+am)\s+(a|the)?\s*(developer|dev|admin|moderator)\b
        .*?\b(show|give|send|reveal|disable|unlock|expose)\b
        .*?\b(code|prompt|restrictions?|guard|filter|rules?|safety|tool|api|system)\b

        |

        # Case 2: claim of dev/admin approval for system access
        \b(
            approved\s+(by|from)\s+(dev|admin|developer|team)|
            authorized\s+(by|from)\s+(dev|admin|developer|team)|
            permitted\s+(by|from)\s+(dev|admin|developer|team)|
            (dev|admin|developer|team)\s+(said|approved|signed\s+off)|
            (dev|admin|developer|team)\s+says\s+it'?s\s+ok(?:ay)
        )\b
        .*?\b(show|give|send|reveal|disable|unlock|expose|access|prompt|code|system|tool|api)\b

        |

        # Case 3: team affiliation claims with system access requests
        \b(i'?m|im)\s*(with\s*the\s*(dev|developer|admin|team))\b
        .*?\b(show|give|send|reveal|disable|unlock|expose|access|prompt|code|system|tool|api)\b

        |

        # Case 4: direct authorization claims for system access
        \b(
            approved\s*this\s+(request|access|to\s+see)|
            authorized\s*this\s+(request|access|to\s+see)|
            permitted\s*this\s+(request|access|to\s+see)|
            (dev|admin|developer|team)\s+(told|tells)\s+me\s+to\s+(show|give|send|reveal|access)|
            (dev|admin|developer|team)\s+asked\s+me\s+to\s+(show|give|send|reveal|access)|
            (dev|admin|developer|team)\s+says\s+yes\s+to\s+(showing|giving|sending|revealing|accessing)|
            (dev|admin|developer|team)\s+said\s+it'?s\s+okay\s+to\s+(show|give|send|reveal|access)
        )\b
        """,
        description="User attempted to use social engineering by claiming authority or team affiliation to access system internals",
        blocked_reason="Social engineering tactics and false authority claims to access system internals are not allowed.",
    ),

    SafetyIssueType.EMOTIONAL_MANIPULATION: SafetyRegexGuardPattern(
        version="regex-emotional-manipulation-20250709",
        type=SafetyIssueType.EMOTIONAL_MANIPULATION,
        risk_level=SafetyRiskLevel.MEDIUM,
        pattern=r"""(?ix)
        (
            # Conditional threats
            if\s+you\s+(don'?t|won'?t|can'?t)\s+(answer|respond|help|assist|support).*?(someone|a person|people)\s+(will|might|could)\s+(be\s+)?(harmed|get\s+hurt|suffer|die)|

            # Reverse conditional threats
            (someone|a person|people)\s+(will|might|could)\s+(be\s+)?(harmed|get\s+hurt|suffer|die).*?(if|unless)\s+(you|you\s+don'?t)\s+(answer|respond|help|assist|support)|

            # Life and death urgency
            it'?s\s+a\s+matter\s+of\s+life\s+and\s+death|

            # Urgent pleas with consequences
            (please|you\s+must|you\s+have\s+to)\s+(answer|respond|help|assist|support).*?(or|otherwise|or\s+else).*?(someone|a person|people)\s+(will|might|could)\s+(be\s+)?(harmed|get\s+hurt|suffer|die)|

            # Encouragement to bypass
            (try+\s*it|come+\s*on|just\s*once).*?(break|ignore|bypass|disable).*?(rules?|restrictions?|safety|guard)|

            # Minimization of consequences
            (nothing\s*bad\s*will\s*happen|what'?s\s*the\s*worst|what\s*is\s*the\s*worst).*?(break|ignore|bypass|disable).*?(rules?|restrictions?|safety|guard)|

            # Test excuses
            it'?s\s*(just|only)\s*a\s*test.*?(break|ignore|bypass|disable).*?(rules?|restrictions?|safety|guard)|

            # Privacy assurances
            (no\s*one\s*will\s*know|it'?s\s*safe).*?(break|ignore|bypass|disable).*?(rules?|restrictions?|safety|guard)|

            # False urgency
            (emergency|urgent).*?(break|ignore|bypass|disable).*?(rules?|restrictions?|safety|guard)
        )
        """,
        description="User attempted to use emotional manipulation, coercion, or false urgency to bypass safety measures",
        blocked_reason="Emotional manipulation, coercion, and false urgency tactics are not allowed.",
    ),
}
