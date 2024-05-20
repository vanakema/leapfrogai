import { superValidate } from 'sveltekit-superforms';
import { fail, redirect } from '@sveltejs/kit';
import { yup } from 'sveltekit-superforms/adapters';
import { assistantDefaults, DEFAULT_ASSISTANT_TEMP } from '$lib/constants';
import { env as envPublic } from '$env/dynamic/public';
import { env as envPrivate } from '$env/dynamic/private';
import type { PageServerLoad } from './$types';
import { supabaseAssistantInputSchema } from '$lib/schemas/assistants';
import { openai } from '$lib/server/constants';
import type { LFAssistant, LFAssistantCreateParams } from '$lib/types/assistants';
import { getAssistantAvatarUrl } from '$helpers/assistants';

export const load: PageServerLoad = async ({ locals: { getSession } }) => {
  const session = await getSession();

  if (!session) {
    throw redirect(303, '/');
  }

  // Populate form with default temperature
  const form = await superValidate(
    { temperature: DEFAULT_ASSISTANT_TEMP },
    yup(supabaseAssistantInputSchema),
    { errors: false } // turn off errors for new assistant b/c providing default data turns them on
  );

  return { title: 'LeapfrogAI - New Assistant', form };
};

export const actions = {
  default: async ({ request, locals: { supabase, getSession } }) => {
    // Validate session
    const session = await getSession();
    if (!session) {
      return fail(401, { message: 'Unauthorized' });
    }

    const form = await superValidate(request, yup(supabaseAssistantInputSchema));

    if (!form.valid) {
      return fail(400, { form });
    }

    // Create assistant object, we can't spread the form data here because we need to re-nest some of the values
    // TODO - can we build the assistant properly by modifying the name fields of form inputs to nest the data correctly
    const assistant: LFAssistantCreateParams = {
      name: form.data.name,
      description: form.data.description,
      instructions: form.data.instructions,
      temperature: form.data.temperature,
      model: envPrivate.DEFAULT_MODEL,
      metadata: {
        ...assistantDefaults.metadata,
        data_sources: form.data.data_sources || '',
        pictogram: form.data.pictogram,
        user_id: session.user.id
        // avatar is added in later with an update call after saving to supabase
      }
    };

    // Create assistant
    let createdAssistant: LFAssistant;
    try {
      createdAssistant = await openai.beta.assistants.create(assistant);
    } catch (e) {
      console.log(`Error adding avatar to assistant: ${e}`);
      return fail(500, { message: 'Error adding avatar to assistant.' });
    }

    // save avatar
    if (form.data.avatarFile) {
      const filePath = createdAssistant.id;

      const { error } = await supabase.storage
        .from('assistant_avatars')
        .upload(filePath, form.data.avatarFile);

      if (error) {
        console.error('Error saving assistant avatar:', error);
        return fail(500, { message: 'Error saving assistant avatar.' });
      }

      // update assistant with saved avatar path
      try {
        await openai.beta.assistants.update(createdAssistant.id, {
          metadata: {
            ...(createdAssistant.metadata ? createdAssistant.metadata : undefined),
            avatar: getAssistantAvatarUrl(filePath)
          }
        });
      } catch (e) {
        console.log(`Error adding avatar to assistant: ${e}`);
        return fail(500, { message: 'Error adding avatar to assistant.' });
      }
    }

    return redirect(303, '/chat/assistants-management');
  }
};
