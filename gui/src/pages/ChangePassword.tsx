import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { changePassword } from '../services/auth';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';

interface ChangePasswordFormData {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export const ChangePassword: React.FC = () => {
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitted, touchedFields },
    watch,
    reset,
  } = useForm<ChangePasswordFormData>({
    mode: 'onSubmit',
    reValidateMode: 'onBlur',
    shouldFocusError: false,
  });

  const newPassword = watch('new_password');

  const onSubmit = async (data: ChangePasswordFormData) => {
    setError('');
    setSuccess('');
    setLoading(true);
    try {
      await changePassword({
        current_password: data.current_password,
        new_password: data.new_password,
      });
      setSuccess('Password changed successfully!');
      reset();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to change password, please check if the current password is correct');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-7rem)] flex flex-col items-center justify-center">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Change Password</h1>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-none border border-transparent dark:border-gray-700 p-6 max-w-md w-full">
        <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
          {error && (
            <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded">
              {error}
            </div>
          )}
          {success && (
            <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-300 px-4 py-3 rounded">
              {success}
            </div>
          )}
          <div className="space-y-4">
            <Input
              label="Current Password"
              type="password"
              {...register('current_password', { required: 'Current password is required' })}
              error={
                isSubmitted || touchedFields.current_password
                  ? errors.current_password?.message
                  : undefined
              }
            />
            <Input
              label="New Password"
              type="password"
              {...register('new_password', {
                required: 'New password is required',
                minLength: {
                  value: 6,
                  message: 'New password must be at least 6 characters',
                },
              })}
              error={
                isSubmitted || touchedFields.new_password
                  ? errors.new_password?.message
                  : undefined
              }
            />
            <Input
              label="Confirm New Password"
              type="password"
              {...register('confirm_password', {
                required: 'Please confirm the new password',
                validate: (value) =>
                  value === newPassword || 'Passwords do not match',
              })}
              error={
                isSubmitted || touchedFields.confirm_password
                  ? errors.confirm_password?.message
                  : undefined
              }
            />
          </div>
          <div>
            <Button
              type="submit"
              variant="primary"
              className="w-full"
              disabled={loading}
            >
              {loading ? 'Changing...' : 'Change Password'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
