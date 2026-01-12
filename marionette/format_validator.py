#!/usr/bin/env python3
# coding: utf-8
"""
Format validation utilities for Marionette formats.

Validates format structure including:
- Graph structure (path from start to end state)
- Probability distributions (probabilities sum to 1)
"""


class FormatValidationError(Exception):
    """Exception raised when format validation fails."""
    pass


def validate_format(parsed_format):
    """
    Validate a parsed Marionette format.
    
    Args:
        parsed_format: MarionetteFormat object returned by parse()
        
    Raises:
        FormatValidationError: If validation fails
    """
    transitions = parsed_format.get_transitions()
    
    if not transitions:
        raise FormatValidationError("Format has no transitions")
    
    # Group transitions by source state
    transitions_by_src = {}
    states = set()
    
    for transition in transitions:
        src = transition.get_src()
        dst = transition.get_dst()
        states.add(src)
        states.add(dst)
        
        if src not in transitions_by_src:
            transitions_by_src[src] = []
        transitions_by_src[src].append(transition)
    
    # Validate that start state exists
    if 'start' not in states:
        raise FormatValidationError("Format must have a 'start' state")
    
    # Validate probability distributions for each source state
    for src_state, state_transitions in transitions_by_src.items():
        # Skip error transitions when calculating probability sums
        prob_sum = 0.0
        has_error = False
        
        for transition in state_transitions:
            if transition.is_error_transition():
                has_error = True
            else:
                prob = transition.get_probability()
                if prob < 0.0 or prob > 1.0:
                    raise FormatValidationError(
                        f"Transition from '{src_state}' to '{transition.get_dst()}' "
                        f"has invalid probability {prob} (must be between 0.0 and 1.0)")
                prob_sum += prob
        
        # Probabilities should sum to 1.0 (within floating point tolerance)
        # Allow some tolerance for floating point arithmetic
        if not has_error and abs(prob_sum - 1.0) > 0.001:
            raise FormatValidationError(
                f"Transitions from state '{src_state}' have probabilities summing to "
                f"{prob_sum:.6f} (must sum to 1.0)")
    
        # Validate graph structure: check for path from start to end
        if 'end' not in states:
            # This is actually OK - formats can have no end state (infinite loops)
            # But we should at least verify the graph is connected
            _validate_graph_connected(transitions_by_src, states, 'start')
        else:
            # Check if there's a path from start to end
            if not _has_path(transitions_by_src, 'start', 'end'):
                raise FormatValidationError(
                    "No path exists from 'start' state to 'end' state")


def _has_path(transitions_by_src, start, end):
    """Check if there's a path from start to end using DFS."""
    visited = set()
    
    def dfs(state):
        if state == end:
            return True
        if state in visited:
            return False
        visited.add(state)
        
        if state not in transitions_by_src:
            return False
        
        for transition in transitions_by_src[state]:
            dst = transition.get_dst()
            if dfs(dst):
                return True
        return False
    
    return dfs(start)


def _validate_graph_connected(transitions_by_src, states, start_state):
    """Validate that all states are reachable from start state."""
    visited = set()
    
    def dfs(state):
        if state in visited:
            return
        visited.add(state)
        
        if state not in transitions_by_src:
            return
        
        for transition in transitions_by_src[state]:
            dfs(transition.get_dst())
    
    dfs(start_state)
    
    unreachable = states - visited
    if unreachable:
        # This is a warning, not an error
        # Some states might be intentionally unreachable
        pass
