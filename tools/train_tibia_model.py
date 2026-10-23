"""Compatibility entry point for the reviewed private-context experiment.

Usage: python3 tools/train_tibia_model.py fit|evaluate
The former whole-text trainer and audit-category label conversion are retired.
"""
import runpy

if __name__ == '__main__':
    runpy.run_module('train_tibia_private', run_name='__main__')
