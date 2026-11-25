"""Structured output Claude must return: the rewritten resume plus an analysis."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SkillGroup(BaseModel):
    category: str = Field(description="e.g. 'Languages', 'Cloud & DevOps'")
    items: list[str]


class Role(BaseModel):
    title: str
    company: str
    location: str = Field(description="Empty string if not in the original")
    dates: str = Field(description="Exactly as in the original, e.g. 'Jan 2021 - Present'")
    bullets: list[str]


class Project(BaseModel):
    name: str
    subtitle: str = Field(description="Tech stack, link or context; empty string if none")
    bullets: list[str]


class Education(BaseModel):
    degree: str
    institution: str
    dates: str
    details: str = Field(description="GPA, honors, coursework; empty string if none")


class ExtraSection(BaseModel):
    heading: str = Field(description="e.g. 'Publications', 'Volunteering', 'Languages'")
    items: list[str]


class Resume(BaseModel):
    name: str
    headline: str = Field(description="Professional title aligned with the target role, if truthful")
    contact: list[str] = Field(description="Email, phone, location, links, copied from the original")
    summary: str
    skills: list[SkillGroup]
    experience: list[Role]
    projects: list[Project]
    education: list[Education]
    certifications: list[str]
    extra_sections: list[ExtraSection]


class RequirementMatch(BaseModel):
    requirement: str = Field(description="One requirement from the job posting, paraphrased briefly")
    status: Literal["strong", "partial", "missing"]
    evidence: str = Field(
        description="Where the resume shows it, or for 'missing', what is absent"
    )


class Gap(BaseModel):
    requirement: str
    suggestion: str = Field(
        description="Honest advice: e.g. mention it in a cover letter, add it if the candidate truly has it, or build it"
    )


class TailorResult(BaseModel):
    target_role: str = Field(description="Job title (and company, if stated) from the posting")
    resume: Resume
    requirements: list[RequirementMatch]
    changes: list[str] = Field(description="Short list of the main edits made and why")
    gaps: list[Gap]
    keywords_used: list[str] = Field(
        description="Keywords from the posting that now appear in the resume, all truthfully supported"
    )
