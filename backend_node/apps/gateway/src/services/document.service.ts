type Doc = {
    id: string;
    userId: string;
    title: string;
    createdAt: string;
};

const docs: Doc[] = [];

const genId = () => Math.random().toString(36).substring(2, 15);

export const getDocuments = async (userId: string): Promise<Doc[]> => {
    return docs.filter((d) => d.userId === userId);
}

export const createDocument = async (userId: string, title: string): Promise<Doc> => {
    const newDoc: Doc = {
        id: genId(),
        userId,
        title,
        createdAt: new Date().toISOString()
    };
    docs.push(newDoc);
    return newDoc;
}

export const getDocumentById = async (userId: string, id: string): Promise<Doc | null> => {
    const doc = docs.find((d) => d.id === id && d.userId === userId);
    return doc || null;
}