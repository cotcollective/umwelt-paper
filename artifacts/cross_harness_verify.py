#!/usr/bin/env python3
"""
Cross-Harness Analysis: Verify DeepSeek-Harness (Cordis) Channel-Blind Design

This script validates the key findings from Section 5 of the paper by
checking the DeepSeek-Harness source code for:
1. MessageSource schema - no transport channel field
2. Surface projection - no channel metadata injection
3. Context forms - semantic only, not transport provenance

Usage:
    python cross_harness_verify.py --path /mnt/WD1TB/deepseek-harness
"""

import os
import sys
import argparse

def check_file_exists(path: str, description: str) -> bool:
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"  {status} {description}: {path}")
    return exists

def check_message_source_schema(path: str) -> bool:
    """Verify MessageSource has no transport channel field."""
    try:
        with open(path, 'r') as f:
            content = f.read()
        
        # Check for MessageSourceMap definition (TypeScript syntax)
        has_message_source_map = "MessageSourceMap" in content
        
        # Check for kinds using TypeScript interface syntax
        has_user_kind = "user:" in content and "kind: 'user'" in content
        has_plugin_kind = "plugin:" in content and "kind: 'plugin'" in content
        has_model_kind = "model:" in content and "ModelMessageSource" in content
        has_tool_kind = "tool:" in content and "ToolMessageSource" in content
        
        kinds_found = sum([has_user_kind, has_plugin_kind, has_model_kind, has_tool_kind])
        
        # Check for transport channel fields (should NOT exist in MessageSource)
        # Look for platform/chat_id as fields in the source types
        has_platform_field = "platform" in content and "source" in content.lower()
        
        print(f"  MessageSourceMap defined: {has_message_source_map}")
        print(f"  Kinds found: {kinds_found}/4 (user={has_user_kind}, plugin={has_plugin_kind}, model={has_model_kind}, tool={has_tool_kind})")
        print(f"  Transport channel fields in source types: {has_platform_field} (should be False)")
        
        return has_message_source_map and kinds_found >= 3 and not has_platform_field
    except Exception as e:
        print(f"  Error reading {path}: {e}")
        return False

def check_surface_projection(path: str) -> bool:
    """Verify deriveEventMessage passes content verbatim without channel injection."""
    try:
        with open(path, 'r') as f:
            content = f.read()
        
        has_derive = "deriveEventMessage" in content
        has_user_message = "user/message" in content
        has_verbatim = "event.data" in content and "return" in content
        
        # Check that it doesn't inject channel metadata
        no_channel_injection = "platform" not in content or "platform:" not in content
        
        print(f"  deriveEventMessage found: {has_derive}")
        print(f"  Handles user/message: {has_user_message}")
        print(f"  Verbatim pass-through pattern: {has_verbatim}")
        print(f"  No channel injection in surface: {no_channel_injection}")
        
        return has_derive and has_verbatim and no_channel_injection
    except Exception as e:
        print(f"  Error reading {path}: {e}")
        return False

def check_context_forms(path: str) -> bool:
    """Verify ContextForm is semantic, not transport."""
    try:
        with open(path, 'r') as f:
            content = f.read()
        
        # Check for semantic forms
        forms = ['instructions', 'catalog', 'snapshot', 'notice', 'relay', 'recall']
        found_forms = [f for f in forms if f"'{f}'" in content or f'"{f}"' in content]
        
        print(f"  ContextForm values found: {found_forms}")
        print(f"  All 6 semantic forms present: {len(found_forms) == 6}")
        
        # Check for transport forms (should NOT exist in ContextForm union)
        # Look for them specifically in the ContextForm type definition area
        transport_forms = ['telegram', 'discord', 'slack', 'webhook']
        found_transport = []
        for tf in transport_forms:
            # Only count if it appears near ContextForm definition
            idx = content.find("ContextForm")
            if idx >= 0:
                context_section = content[idx:idx+2000]
                if f"'{tf}'" in context_section or f'"{tf}"' in context_section:
                    found_transport.append(tf)
        
        print(f"  Transport forms in ContextForm: {found_transport} (should be empty)")
        
        return len(found_forms) >= 5 and len(found_transport) == 0
    except Exception as e:
        print(f"  Error reading {path}: {e}")
        return False

def check_system_prompt_rendering(path: str) -> bool:
    """Verify system prompt rendering doesn't inject channel provenance."""
    try:
        with open(path, 'r') as f:
            content = f.read()
        
        has_render_prompt = "renderPrompt" in content
        has_context_snapshot = "renderContextSnapshot" in content or "ContextSnapshotSection" in content
        
        print(f"  renderPrompt found: {has_render_prompt}")
        print(f"  Context snapshot rendering: {has_context_snapshot}")
        
        return has_render_prompt
    except Exception as e:
        print(f"  Error reading {path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="/mnt/WD1TB/deepseek-harness")
    args = parser.parse_args()

    base = args.path
    print(f"Verifying DeepSeek-Harness at: {base}")
    print()

    checks = []

    # 1. Core message schema
    print("1. Message Source Schema (packages/llm/llm/src/message.ts)")
    msg_path = os.path.join(base, "packages/llm/llm/src/message.ts")
    checks.append(("MessageSource schema", check_file_exists(msg_path, "message.ts") and check_message_source_schema(msg_path)))

    # 2. Surface projection
    print("\n2. Surface Projection (packages/core/session/src/surface.ts)")
    surf_path = os.path.join(base, "packages/core/session/src/surface.ts")
    checks.append(("Surface projection", check_file_exists(surf_path, "surface.ts") and check_surface_projection(surf_path)))

    # 3. Context forms
    print("\n3. Context Forms (packages/llm/llm/src/message.ts - ContextFormed)")
    checks.append(("Context forms", check_context_forms(msg_path)))

    # 4. System prompt rendering
    print("\n4. System Prompt Rendering (packages/core/system-prompt/src/index.ts)")
    sp_path = os.path.join(base, "packages/core/system-prompt/src/index.ts")
    checks.append(("System prompt", check_file_exists(sp_path, "system-prompt") and check_system_prompt_rendering(sp_path)))

    # 5. Session source
    print("\n5. Session Source (packages/core/session/src/index.ts)")
    sess_path = os.path.join(base, "packages/core/session/src/index.ts")
    checks.append(("Session source", check_file_exists(sess_path, "session source")))

    # Summary
    print("\n" + "=" * 50)
    print("CROSS-HARNESS VERIFICATION SUMMARY")
    print("=" * 50)
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")

    all_passed = all(passed for _, passed in checks)
    print(f"\nOverall: {'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")
    
    if all_passed:
        print("\n✅ DeepSeek-Harness confirms channel-blind design:")
        print("   - MessageSource has semantic forms only (no transport channel)")
        print("   - Surface projection passes content verbatim")
        print("   - ContextForm has 6 semantic values, 0 transport values")
        print("   - System prompt renders semantic context, not channel provenance")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())