# Enterprise AI Agent – Architecture

## Overview
The Enterprise AI Agent is designed to automate business workflows using a modular, multi-agent system. 
It can summarize documents, calculate KPIs, generate emails, extract JSON, and read files.

## Components

1. **Main Agent (`main_agent.py`)**
   - Handles all generic tasks.
   - Integrates multiple tools: JSONExtractorTool, KPITool, BusinessSummaryTool, EmailGeneratorTool, FileReaderTool.
   - Uses MemoryService for session-based memory storage.

2. **Tools (`enterprise_tools.py`)**
   - JSONExtractorTool: Cleans and extracts JSON from LLM outputs.
   - KPITool: Calculates profit, margin, conversion rate.
   - BusinessSummaryTool: Summarizes documents and reports.
   - EmailGeneratorTool: Creates structured email content.
   - FileReaderTool: Reads text files.

3. **Memory Service (`memory_service.py`)**
   - SessionMemory: Stores short-term session history.
   - MemoryBank: Long-term persistent memory storage.
   - Context compaction: Keeps only important/recent messages for efficiency.

4. **Multi-Agent Orchestrator (`multi_agent.py`)**
   - Routes tasks to specialized agents (KPI Agent, Summary Agent, Email Agent, JSON Agent, File Agent).

5. **API (`server.py`)**
   - FastAPI server to expose Gemini-powered enterprise tools.
   - Allows querying employee data and integrates Gemini functions.
