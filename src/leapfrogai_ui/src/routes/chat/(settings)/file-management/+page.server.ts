import type { PageServerLoad } from './$types';
import { fail, json, redirect } from '@sveltejs/kit';
import { openai } from '$lib/server/constants';
import { message, superValidate, withFiles } from 'sveltekit-superforms';
import { yup } from 'sveltekit-superforms/adapters';
import { filesSchema } from '$schemas/files';
import type { FileObject } from 'openai/src/resources/files';
import type { FileRow } from '$lib/types/files';
import { getUnixSeconds } from '$helpers/dates';

export const load: PageServerLoad = async ({ locals: { getSession } }) => {
  const session = await getSession();

  if (!session) {
    throw redirect(303, '/');
  }

  const list = await openai.files.list();
  const form = await superValidate(yup(filesSchema));

  return { title: 'LeapfrogAI - File Management', files: list.data, form };
};

export const actions = {
  default: async ({ request }) => {
    const form = await superValidate(request, yup(filesSchema));

    if (!form.valid) {
      console.log(form.errors);
      return fail(400, { form });
    }

    if (form.data.files) {
      const uploadedFiles: Array<FileObject | FileRow> = [];
      for (const file of form.data.files) {
        if (file) {
          try {
            if (file.name === 'Resume.pdf') throw Error('error');
            const uploadedFile = await openai.files.create({
              file: file,
              purpose: 'assistants'
            });
            uploadedFiles.push(uploadedFile);
          } catch (e) {
            console.error(`Error uploading file ${file.name}: ${e}`);
            const item: FileRow = {
              id: `${file.name}-error-${new Date()}`,
              filename: file.name,
              created_at: getUnixSeconds(new Date()),
              status: 'error'
            };

            uploadedFiles.push(item);
          }
        }
      }

      return withFiles({ form, uploadedFiles });
    }
  }
};
