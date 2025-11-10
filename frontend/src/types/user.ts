export interface User {
    id: number;
    email: string;
    name: string;
    role: string;
    language: string;
    preferred_text_model: string;
    preferred_image_model: string;
    created_at?: string;
    updated_at?: string;
}

export interface OllamaModel {
    name: string;
    size: number;
    digest?: string;
    modified_at?: string;
}

export interface OllamaStatus {
    installed: boolean;
    version: string | null;
    error: string | null;
}

export interface AvailableModels {
    text: OllamaModel[];
    image: OllamaModel[];
}

export interface RecommendedModel {
    name: string;
    type: 'text' | 'image';
    description: string;
}

export interface RecommendedModels {
    low: RecommendedModel[];
    medium: RecommendedModel[];
    high: RecommendedModel[];
}

export interface PerformanceProfile {
    name: string;
    description: string;
    recommended_models: string[];
    min_ram: string;
    min_storage: string;
}

export interface InstallerInfo {
    download_url: string;
    installer_file: string;
    performance_profiles: {
        low: PerformanceProfile;
        medium: PerformanceProfile;
        high: PerformanceProfile;
    };
    installation_steps: string[];
} 