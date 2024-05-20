import { error, fail, redirect } from '@sveltejs/kit';
import { superValidate } from 'sveltekit-superforms';
import type { PageServerLoad } from './$types';
import { yup } from 'sveltekit-superforms/adapters';
import { editAssistantInputSchema } from '$lib/schemas/assistants';
import { env } from '$env/dynamic/private';
import { assistantDefaults, DEFAULT_ASSISTANT_TEMP } from '$lib/constants';
import { openai } from '$lib/server/constants';
import type { EditAssistantInput, LFAssistant } from '$lib/types/assistants';

export const load: PageServerLoad = async ({ params, locals: { getSession, supabase } }) => {
  const session = await getSession();

  if (!session) {
    throw redirect(303, '/');
  }

  const assistant = (await openai.beta.assistants.retrieve(params.assistantId)) as LFAssistant;

  if (!assistant) {
    error(404, { message: 'Assistant not found.' });
  }

  const assistantFormData: EditAssistantInput = {
    id: assistant.id,
    name: assistant.name || '',
    description: assistant.description || '',
    instructions: assistant.instructions || '',
    temperature: assistant.temperature || DEFAULT_ASSISTANT_TEMP,
    data_sources: assistant.metadata.data_sources,
    pictogram: assistant.metadata.pictogram,
    avatar: assistant.metadata.avatar
  };

  const form = await superValidate(assistantFormData, yup(editAssistantInputSchema));

  return { title: 'LeapfrogAI - Edit Assistant', form, assistant };
};

export const actions = {
  default: async ({ request, locals: { supabase, getSession } }) => {
    // Validate session
    const session = await getSession();
    if (!session) {
      return fail(401, { message: 'Unauthorized' });
    }

    let savedAvatarFilePath: string = '';

    const form = await superValidate(request, yup(editAssistantInputSchema));

    if (!form.valid) {
      return fail(400, { form });
    }

    // Update avatar if new file uploaded
    if (typeof form.data.avatar === 'object') {
      const filePath = form.data.id;

      const { data: supabaseData, error } = await supabase.storage
        .from('assistant_avatars')
        .upload(filePath, form.data.avatar, { upsert: true });

      if (error) {
        console.error('Error updating assistant avatar:', error);
        return fail(500, { message: 'Error updating assistant avatar.' });
      }

      savedAvatarFilePath = supabaseData.path;
    } else {
      if (!form.data.avatar) {
        // Delete avatar
        const { error: deleteAvatarError } = await supabase.storage
          .from('avatars')
          .remove(['folder/avatar1.png']);
        if (deleteAvatarError) return fail(500, { message: 'error deleting avatar' });
      }
    }

    // Create assistant object
    const assistant: Partial<LFAssistant> = {
      name: form.data.name,
      description: form.data.description,
      instructions: form.data.instructions,
      temperature: form.data.temperature,
      model: env.DEFAULT_MODEL,
      metadata: {
        ...assistantDefaults.metadata,
        data_sources: form.data.data_sources || '',
        avatar: savedAvatarFilePath,
        pictogram: form.data.pictogram,
        user_id: session.user.id
      }
    };

    // Update assistant
    try {
      await openai.beta.assistants.update(form.data.id, assistant);
    } catch (e) {
      console.log(`Error updating assistant: ${e}`);
      return fail(500, { message: 'Error updating assistant.' });
    }

    return redirect(303, '/chat/assistants-management');
  }
};
